# função handle_message
from . import service, catalog, pedidos, atendimento, qualificacao, marketing
import json
import logging
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from ..integrations.openai_client import generate_response
from ..integrations.supabase_store import fetch_recent_messages_by_telefone
from ..integrations.google_knowledge import build_context_for_intent

# Contexto para agentes
@dataclass
class AgentContext:
    message: str
    phone: str
    conversation_history: List[Dict[str, Any]]
    google_context: Dict[str, Any]
    
logger = logging.getLogger("3afrios.orchestrator")

def _bruno_analyze_conversation(message: str, conversation_history: List[Dict], context: Dict) -> Dict[str, Any]:
    """
    Bruno Analista Invisível - Qualifica leads silenciosamente em background
    Analisa conversas e gera insights para outros agentes
    """
    try:
        # Extrai dados da conversa para análise
        recent_messages = [item.get('mensagem_cliente', '') for item in conversation_history[-5:]]
        full_conversation = ' '.join(recent_messages + [message]).lower()
        
        # === ANÁLISE DE PERFIL DO CLIENTE ===
        
        # Detecta segmento
        segmento = 'pessoa_fisica'  # default
        if any(word in full_conversation for word in ['empresa', 'restaurante', 'cnpj', 'corporativo']):
            segmento = 'pessoa_juridica'
        elif any(word in full_conversation for word in ['casamento', 'festa', 'evento', 'formatura']):
            segmento = 'evento_especial'
        
        # Detecta urgência
        urgencia = 'baixa'
        if any(word in full_conversation for word in ['hoje', 'amanhã', 'urgente', 'rápido']):
            urgencia = 'alta'
        elif any(word in full_conversation for word in ['semana', 'próxima']):
            urgencia = 'media'
        
        # Detecta interesse de compra
        interesse_compra = 0
        if any(word in full_conversation for word in ['quero', 'preciso', 'vou levar', 'comprar']):
            interesse_compra += 3
        if any(word in full_conversation for word in ['quanto', 'preço', 'valor', 'custa']):
            interesse_compra += 2
        if any(word in full_conversation for word in ['produto', 'catálogo', 'tem']):
            interesse_compra += 1
            
        # Detecta quantidade de pessoas
        pessoas = None
        import re
        pessoas_match = re.search(r'(\d+)\s*pessoas?', full_conversation)
        if pessoas_match:
            pessoas = int(pessoas_match.group(1))
        
        # === SCORE DO LEAD ===
        lead_score = min(10, interesse_compra)
        if urgencia == 'alta':
            lead_score += 2
        if segmento == 'pessoa_juridica':
            lead_score += 1
        if pessoas and pessoas > 20:
            lead_score += 1
            
        # === INSIGHTS PARA OS AGENTES ===
        insights = {
            'lead_score': lead_score,
            'segmento': segmento,
            'urgencia': urgencia,
            'interesse_compra': interesse_compra,
            'pessoas': pessoas,
            'qualificacao_status': 'hot' if lead_score >= 7 else 'warm' if lead_score >= 4 else 'cold',
            'sugestoes_agente': []
        }
        
        # Sugestões específicas por score
        if lead_score >= 7:  # Hot lead
            insights['sugestoes_agente'].append("🔥 LEAD QUENTE - Priorizar fechamento")
            insights['sugestoes_agente'].append("💰 Oferecer condições especiais")
            if urgencia == 'alta':
                insights['sugestoes_agente'].append("⚡ URGENTE - Processar rapidamente")
        elif lead_score >= 4:  # Warm lead  
            insights['sugestoes_agente'].append("🌡️ LEAD MORNO - Nutrir interesse")
            insights['sugestoes_agente'].append("📋 Fazer perguntas qualificadoras")
        else:  # Cold lead
            insights['sugestoes_agente'].append("❄️ LEAD FRIO - Educar sobre produtos")
            insights['sugestoes_agente'].append("🎁 Oferecer valor antes da venda")
            
        # Sugestões específicas por segmento
        if segmento == 'pessoa_juridica':
            insights['sugestoes_agente'].append("🏢 B2B - Falar sobre volume e regularidade")
        elif segmento == 'evento_especial':
            insights['sugestoes_agente'].append("🎉 EVENTO - Oferecer serviço completo")
            
        logger.info(f"[Bruno Invisible] Lead analisado: score={lead_score}, segmento={segmento}, status={insights['qualificacao_status']}")
        
        return insights
        
    except Exception as e:
        logger.error(f"[Bruno Invisible] Erro na análise: {e}")
        return None


INTENT_KEYWORDS: Dict[str, List[str]] = {
    'Catálogo': [
        'catálogo', 'catalogo', 'produto', 'produtos', 'preço', 'disponibilidade',
        'tem', 'possui', 'vende', 'quanto', 'custa', 'valor', 'cardápio', 'cardapio',
        'menu', 'lista', 'oferece', 'disponível', 'disponivel',
        'carne', 'carnes', 'frango', 'peixe', 'peixes', 'porco', 'boi',
        'galinha', 'aves', 'frios', 'queijo', 'queijos', 'presunto',
        'mortadela', 'salame', 'linguiça', 'linguica'
    ],
    'Pedidos': [
        'pedido', 'comprar', 'finalizar', 'ordem', 'adicionar', 'carrinho',
        'quero', 'preciso', 'encomenda', 'encomendar', 'fazer pedido'
    ],
    'Atendimento': [
        'troca', 'devolução', 'prazo', 'entrega', 'horário', 'atendimento', 
        'suporte', 'reclamação', 'endereço', 'problema', 'ajuda', 'dúvida',
        'contato', 'telefone', 'email'
    ],
    'Marketing': [
        'campanha', 'promoção', 'promocao', 'desconto', 'marketing',
        'anúncio', 'newsletter', 'oferta', 'novidade'
    ],
}

def _score_intent(text: str) -> Tuple[str, int, List[str]]:
    text = text.lower().strip()
    best_intent = None
    best_score = 0
    matched_terms: List[str] = []

    # === NOVO: Detecção inteligente de PEDIDOS ===
    # Gatilhos fortes de intenção de compra
    gatilhos_pedido = [
        'quero', 'vou querer', 'vou levar', 'preciso de', 'gostaria de',
        'me vende', 'venda', 'comprar', 'fazer pedido', 'encomenda',
        'solicitar', 'adquirir'
    ]
    
    # Indicadores de quantidade (forte sinal de pedido)
    indicadores_quantidade = [
        'quilo', 'kg', 'gramas', 'unidade', 'peça', 'pacote', 'caixa',
        'um quilo', 'dois quilos', 'meio quilo', '500g', '1kg', '2kg',
        'uma unidade', 'duas unidades', 'três'
    ]
    
    # Verbos de ação de compra
    verbos_compra = [
        'levar', 'pedir', 'encomendar', 'solicitar', 'reservar'
    ]

    # Lista de produtos/termos comuns (sem acento para robustez)
    produtos_genericos = [
        'carne', 'carnes', 'frango', 'peixe', 'peixes', 'porco', 'suino', 'suína', 'bovino',
        'boi', 'galinha', 'aves', 'frios', 'queijo', 'queijos', 'presunto', 'mortadela',
        'salame', 'linguica', 'linguiça', 'salsicha', 'calabresa', 'pernil', 'file', 'filé'
    ]

    # Gatilhos de pedido de catálogo/lista
    gatilhos_catalogo = [
        'catalogo', 'catálogo', 'lista de produtos', 'me envia o catalogo', 'me mande o catalogo',
        'manda o catalogo', 'enviar catalogo', 'ver catalogo', 'catálogo de produtos'
    ]

    # Gatilhos de pergunta sobre produto (sem intenção de compra)
    perguntas_produtos = [
        'tem ', 'têm ', 'teria ', 'teriam ',
        'vocês tem', 'vcs tem', 'voces tem',
        'vocês têm', 'vcs têm', 'voces têm',
        'quais tipos', 'que tipos',
        'vendem', 'vende', 'trabalha com',
        'quanto custa', 'qual valor', 'qual preço', 'qual preco'
    ]

    # === PRIORIDADE 1: PEDIDOS (intenção de compra clara) ===
    # Se tem gatilho de pedido + produto/quantidade = PEDIDO
    has_pedido_trigger = any(trg in text for trg in gatilhos_pedido)
    has_quantidade = any(ind in text for ind in indicadores_quantidade)
    has_verbo_compra = any(verb in text for verb in verbos_compra)
    has_produto = any(prod in text for prod in produtos_genericos)
    
    # Casos de PEDIDO com alta confiança
    if (has_pedido_trigger and (has_produto or has_quantidade)) or \
       (has_quantidade and has_produto) or \
       (has_verbo_compra and has_produto):
        matched = []
        if has_pedido_trigger:
            matched.extend([t for t in gatilhos_pedido if t in text])
        if has_quantidade:
            matched.extend([t for t in indicadores_quantidade if t in text])
        if has_produto:
            matched.extend([t for t in produtos_genericos if t in text])
        return 'Pedidos', 5, matched  # 5 => confiança muito alta (1.25, mas limitada a 1.0)

    # === PRIORIDADE 2: CATÁLOGO (consultas) ===
    # 1) Solicitação explícita de catálogo: confiança alta
    if any(trg in text for trg in gatilhos_catalogo):
        matched = [trg for trg in gatilhos_catalogo if trg in text]
        return 'Catálogo', 4, matched  # 4 => confiança 1.0 (0.25*4)

    # 2) Pergunta de produto + algum termo de produto: confiança alta
    if any(p in text for p in perguntas_produtos):
        for prod in produtos_genericos:
            if prod in text:
                return 'Catálogo', 4, ['produto', prod]

    # 3) Apenas menciona produtos (sem pergunta): confiança média
    for prod in produtos_genericos:
        if prod in text:
            return 'Catálogo', 3, [prod]  # 3 => confiança 0.75

    # === PRIORIDADE 3: Heurística padrão por keywords ===
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for k in keywords if k.lower() in text)
        if score > best_score:
            best_intent = intent
            best_score = score
            matched_terms = [k for k in keywords if k.lower() in text]

    # === FALLBACK ===
    if not best_intent:
        best_intent = 'Atendimento'

    return best_intent, best_score, matched_terms

async def classify_intent_llm(self, context: AgentContext) -> str:
    """
    Classificação inteligente com OpenAI usando contexto conversacional
    """
    message = context.message
    
    if not message or not message.strip():
        return 'Atendimento'
    
    # Construir contexto da conversa para a OpenAI
    conversation_context = ""
    if context.conversation_history:
        recent_history = context.conversation_history[-4:]  # Últimas 4 interações
        conversation_context = "\n".join([
            f"Cliente: {msg.get('mensagem_cliente', '')}" if msg.get('mensagem_cliente') 
            else f"Bot: {msg.get('resposta_bot', '')}"
            for msg in recent_history
        ])
        conversation_context = f"\nContexto da conversa:\n{conversation_context}\n"
    
    prompt = f"""Você é o orquestrador inteligente da 3A Frios, empresa de carnes, frios e derivados.

AGENTES DISPONÍVEIS:
- Catálogo: Consultas sobre produtos, preços, disponibilidade ("tem carne?", "quais queijos?", "catalogo")
- Pedidos: Intenção clara de compra/solicitação ("quero 1kg", "vou levar", "me vende", "fazer pedido")
- Atendimento: Saudações, dúvidas gerais, reclamações, informações da empresa
- Marketing: Promoções, ofertas, descontos, campanhas

REGRAS DE CLASSIFICAÇÃO:
1. PEDIDOS tem prioridade quando há verbos de ação + produto/quantidade
2. CATÁLOGO para perguntas sobre produtos sem intenção de compra imediata
3. ATENDIMENTO para conversas gerais, problemas, informações

{conversation_context}

Mensagem atual: "{message}"

Responda APENAS com o nome do agente: Catálogo, Pedidos, Atendimento ou Marketing."""

    try:
        from ..integrations.openai_client import generate_response
        response = generate_response(prompt, message)
        
        # Limpar resposta e validar
        intent = response.strip().replace('"', '').replace("'", '')
        valid_intents = ['Catálogo', 'Pedidos', 'Atendimento', 'Marketing']
        
        if intent in valid_intents:
            return intent
        else:
            # Fallback: tentar extrair da resposta
            for valid_intent in valid_intents:
                if valid_intent.lower() in response.lower():
                    return valid_intent
            return 'Atendimento'  # Fallback padrão
            
    except Exception as e:
        logger.error(f"[CLASSIFY_LLM] Erro na OpenAI: {e}")
        return 'Atendimento'

# Substitui a versão anterior para retornar metadados ricos
def route_to_agent(message: str) -> Dict[str, Any]:
    text = (message or '').lower()
    intent, score, terms = _score_intent(text)
    confidence = min(1.0, 0.25 * score)  # 0, 0.25, 0.5, 0.75, 1.0
    if score == 0:
        # Fallback simples sem async por compatibilidade
        llm_intent = 'Atendimento'  # Default quando heurística falha
        confidence = 0.5
        intent = llm_intent
    return {
        'intent': intent,
        'confidence': confidence,
        'matched_terms': terms,
    }


class SmartOrchestrator:
    """
    Orquestrador inteligente com roteamento híbrido
    """
    
    async def route_to_agent(self, context: AgentContext) -> Tuple[str, str, bool]:
        """
        Roteamento híbrido melhorado:
        1. Heurística inteligente com priorização de intenções
        2. OpenAI para casos ambíguos ou complexos  
        3. Contexto conversacional
        """
        current_message = context.message.strip()
        
        # === STEP 1: Heurística inteligente ===
        intent, score, matched_terms = _score_intent(current_message)
        confidence = min(score * 0.25, 1.0)  # Normaliza para [0, 1]
        
        logger.info(f"[ROTEAMENTO] Heurística: '{intent}' (score={score}, conf={confidence:.2f}) | termos: {matched_terms}")
        
        # === STEP 2: Critério para usar OpenAI ===
        # Use OpenAI quando:
        # - Confiança baixa (< 0.5)
        # - Mensagem complexa/longa (> 50 chars com múltiplas palavras)
        # - Contexto de conversa existente
        # - Termos ambíguos detectados
        
        usar_openai = False
        razao_openai = ""
        
        if confidence < 0.5:
            usar_openai = True
            razao_openai = f"baixa confiança ({confidence:.2f})"
        
        elif len(current_message) > 50 and len(current_message.split()) > 8:
            usar_openai = True
            razao_openai = "mensagem complexa/longa"
        
        elif len(context.conversation_history) > 2:
            # Se há histórico, pode haver contexto que muda o sentido
            usar_openai = True
            razao_openai = "contexto conversacional"
        
        # Casos especiais onde sempre usar heurística (alta confiança)
        if confidence >= 0.9:
            usar_openai = False
            razao_openai = "confiança muito alta - heurística suficiente"
        
        # === STEP 3: Execução do roteamento ===
        if usar_openai:
            logger.info(f"[ROTEAMENTO] Usando OpenAI por: {razao_openai}")
            try:
                llm_intent = await self.classify_intent_llm(context)
                
                # Combinar insights: se LLM discorda da heurística em casos limítrofes
                if confidence < 0.6 and llm_intent != intent:
                    logger.info(f"[ROTEAMENTO] LLM discorda: '{llm_intent}' vs heurística '{intent}' - usando LLM")
                    return llm_intent, f"🤖 Análise AI: {razao_openai}", True
                elif confidence >= 0.6:
                    logger.info(f"[ROTEAMENTO] LLM concorda ou heurística confiável - usando heurística")
                    return intent, f"🎯 Roteamento inteligente: {', '.join(matched_terms)}", True
                else:
                    return llm_intent, f"🤖 Análise AI: {razao_openai}", True
                    
            except Exception as e:
                logger.error(f"[ROTEAMENTO] Erro na OpenAI: {e}")
                # Fallback para heurística
                return intent, f"⚡ Roteamento rápido (AI indisponível): {', '.join(matched_terms)}", True
        
        else:
            logger.info(f"[ROTEAMENTO] Usando heurística: {razao_openai}")
            return intent, f"🎯 Roteamento inteligente: {', '.join(matched_terms)}", True

# Atualiza para usar roteamento com confiança, override e normalização de telefone
async def handle_message(payload: dict) -> dict:
    import logging
    logger = logging.getLogger("3afrios.backend")
    
    logger.info("[Orchestrator] Iniciando processamento de mensagem")
    acao = payload.get('acao', 'desconhecida')
    mensagem = payload.get('mensagem', '')
    telefone_raw = (
        payload.get('telefone')
        or payload.get('telefoneCliente')
        or (payload.get('cliente') or {}).get('telefone')
        or ''
    )
    cliente_id_raw = payload.get('clienteId')  # novo: id do cliente vindo do Dashboard
    dry_run = bool(payload.get('dryRun'))
    
    logger.debug(f"[Orchestrator] Dados recebidos: acao={acao} telefone={telefone_raw} msg_len={len(mensagem)}")

    telefone_normalizado = ''.join(ch for ch in str(telefone_raw) if ch.isdigit())
    historico = await fetch_recent_messages_by_telefone(telefone_normalizado or telefone_raw, limit=6)

    contexto_curto = []
    for item in historico[:6]:
        mc = (item.get('mensagem_cliente') or '').strip()
        rb = (item.get('resposta_bot') or '').strip()
        if mc:
            contexto_curto.append(f"C: {mc}")
        if rb:
            contexto_curto.append(f"B: {rb}")

    # Detecta sessão manual ativa por histórico
    sessao_manual = _manual_session_active(historico, ttl_minutes=15)

    if acao == 'responder-manual':
        return {
            'ok': True,
            'acao': acao,
            'dryRun': dry_run,
            'cliente': { 'telefone': telefone_normalizado or telefone_raw, 'id': cliente_id_raw },
            'mensagem_cliente': '',
            'resposta_bot': mensagem,
            'agente_responsavel': 'Operador',
            'routing': { 'intent': 'Manual', 'confidence': 1.0 },
            'acao_especial': 'mensagem_manual_dashboard',
            'contexto_conversa': contexto_curto,
            'memory_used': bool(historico),
            'info': 'Dashboard: resposta manual enviada',
        }

    override = (payload.get('target_agent') or '').strip()
    routing = route_to_agent(mensagem)
    agente_responsavel = override if override in INTENT_KEYWORDS else routing['intent']
    
    logger.info(f"[Orchestrator] Roteamento: agente={agente_responsavel} confiança={routing.get('confidence')} override={bool(override)}")

    # Viés de roteamento baseado no histórico: se repetiu 2+ vezes e confiança baixa
    try:
        last_agents = [i.get('agente_responsavel') for i in historico if i.get('agente_responsavel')]
        if last_agents:
            from collections import Counter
            top_agent, top_count = Counter(last_agents).most_common(1)[0]
            if top_count >= 2 and routing.get('confidence', 0.0) < 0.5 and top_agent in INTENT_KEYWORDS:
                agente_responsavel = top_agent
                routing['confidence'] = max(routing.get('confidence', 0.0), 0.6)
    except Exception:
        pass

    mapping = {
        'Catálogo': catalog,
        'Pedidos': pedidos,
        'Atendimento': atendimento,
        'Marketing': marketing,
    }
    agent_mod = mapping.get(agente_responsavel, atendimento)

    # NOVO: contexto do Google para o agente
    contexto_google = build_context_for_intent(agente_responsavel)

    # === BRUNO ANALISTA INVISÍVEL ===
    # Análise silenciosa em background para qualificar leads
    bruno_insights = None
    try:
        bruno_insights = _bruno_analyze_conversation(mensagem, historico, contexto_google)
        if bruno_insights:
            # Injeta insights do Bruno no contexto do agente
            contexto_google['bruno_insights'] = bruno_insights
            logger.info(f"[Bruno Invisible] Insights gerados: score={bruno_insights.get('lead_score', 'N/A')}, status={bruno_insights.get('qualificacao_status', 'N/A')}")
    except Exception as e:
        logger.error(f"[Bruno Invisible] Erro na análise: {e}")

    # Passa contexto para o agente
    try:
        logger.debug(f"[Orchestrator] Chamando agente {agente_responsavel}")
        logger.debug(f"[Orchestrator] Contexto da conversa: {json.dumps(contexto_curto, ensure_ascii=False)}")
        svc = agent_mod.respond(mensagem, context=contexto_google)
        logger.debug(f"[Orchestrator] Resposta do agente: len={len(svc.get('resposta', ''))} acao={svc.get('acao_especial')}")
    except Exception as e:
        logger.error(f"[Orchestrator] Erro ao processar resposta do agente: {str(e)}", exc_info=True)
        raise

    contexto_curto = []
    for item in historico[:6]:
        mc = (item.get('mensagem_cliente') or '').strip()
        rb = (item.get('resposta_bot') or '').strip()
        if mc:
            contexto_curto.append(f"C: {mc}")
        if rb:
            contexto_curto.append(f"B: {rb}")

    return {
        'ok': True,
        'acao': acao,
        'dryRun': dry_run,
        'cliente': {
            'telefone': telefone_normalizado or telefone_raw,
            'id': cliente_id_raw,
        },
        'mensagem_cliente': mensagem,
        'resposta_bot': svc['resposta'],
        'agente_responsavel': agente_responsavel,
        'routing': routing,
        'acao_especial': svc.get('acao_especial'),
        'contexto_conversa': contexto_curto,
        'memory_used': bool(historico),
        'bruno_insights': bruno_insights,  # Insights do Bruno Invisível
        'info': 'Backend FastAPI: Orquestrador v3 (Bruno Analista Invisível + memória + GoogleCtx)',
    }


def _manual_session_active(historico: List[dict], ttl_minutes: int = 15) -> bool:
    # Sessão manual se houve resposta de 'Operador' nos últimos ttl_minutes
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for it in historico or []:
            if (it.get('agente_responsavel') or '').strip() == 'Operador':
                ts = (it.get('timestamp') or '').strip()
                if not ts:
                    continue
                try:
                    # Suporta ISO com 'Z'
                    ts_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    delta = now - ts_dt
                    if delta.total_seconds() <= ttl_minutes * 60:
                        return True
                except Exception:
                    continue
    except Exception:
        pass
    return False