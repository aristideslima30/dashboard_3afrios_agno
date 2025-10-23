# função handle_message
from . import service, catalog, pedidos, atendimento, qualificacao, marketing
import json
from typing import Dict, Any, List, Tuple
from ..integrations.openai_client import generate_response
from ..integrations.supabase_store import fetch_recent_messages_by_telefone
from ..integrations.google_knowledge import build_context_for_intent


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
    'Qualificação': [
        'qualificar', 'interesse', 'orçamento', 'perfil', 'segmento',
        'informação', 'informações', 'detalhes'
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
    
    # Lista de produtos genéricos para detectar perguntas sobre produtos
    produtos_genericos = [
        'carne', 'carnes', 'frango', 'peixe', 'peixes', 'porco',
        'boi', 'galinha', 'aves', 'frios', 'queijo', 'queijos',
        'presunto', 'mortadela', 'salame', 'linguiça', 'linguica'
    ]
    
    # Primeiro verifica perguntas sobre produtos específicos
    perguntas_produtos = [
        'tem ', 'têm ', 'teria ', 'teriam ',
        'vocês tem', 'vcs tem', 'voces tem',
        'vocês têm', 'vcs têm', 'voces têm',
        'quais tipos', 'que tipos',
        'vendem', 'vende', 'trabalha com',
        'quanto custa', 'qual valor', 'qual preço'
    ]
    
    # Se for pergunta sobre produto, já define como Catálogo
    for p in perguntas_produtos:
        if p in text:
            for prod in produtos_genericos:
                if prod in text:
                    return 'Catálogo', 1, [p, prod]
    
    # Tenta match com palavras-chave normais
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for k in keywords if k.lower() in text)
        if score > best_score:
            best_intent = intent
            best_score = score
            matched_terms = [k for k in keywords if k.lower() in text]
    
    # Se não encontrou nada específico mas menciona algum produto, vai pro Catálogo
    if best_score == 0:
        for prod in produtos_genericos:
            if prod in text:
                return 'Catálogo', 0.8, [prod]
        
        # Outras perguntas genéricas sobre produtos
        if any(p.strip() in text for p in perguntas_produtos):
            return 'Catálogo', 0.6, []
    
    # Se ainda não encontrou nada, usa Atendimento como fallback
    if not best_intent:
        best_intent = 'Atendimento'
        
    return best_intent, best_score, matched_terms

def classify_intent_llm(message: str) -> Dict[str, Any]:
    if not (message or '').strip():
        return {}
    prompt = (
        'Você é o orquestrador da 3A Frios. Classifique a intenção do usuário em uma das opções: '
        'Catálogo, Pedidos, Atendimento, Qualificação, Marketing. Responda em JSON, com os campos '
        'intent (string), confidence (0-1) e reason (string).'
    )
    raw = generate_response(prompt, message or '')
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

# Substitui a versão anterior para retornar metadados ricos
def route_to_agent(message: str) -> Dict[str, Any]:
    text = (message or '').lower()
    intent, score, terms = _score_intent(text)
    confidence = min(1.0, 0.25 * score)  # 0, 0.25, 0.5, 0.75, 1.0
    if score == 0:
        llm = classify_intent_llm(message)
        llm_intent = llm.get('intent')
        if llm_intent in INTENT_KEYWORDS:
            intent = llm_intent
            confidence = float(llm.get('confidence', 0.5))
    return {
        'intent': intent,
        'confidence': confidence,
        'matched_terms': terms,
    }

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
            # Não sobrescreve quando há sinais fortes de Catálogo no texto atual
            text_lower = (mensagem or '').lower()
            strong_product_signal = (routing.get('intent') == 'Catálogo') or any(k in text_lower for k in ['catálogo','catalogo','produto','produtos','preço','preco','valor','lista','cardápio','cardapio'])
            if top_count >= 2 and routing.get('confidence', 0.0) < 0.5 and top_agent in INTENT_KEYWORDS and not strong_product_signal:
                agente_responsavel = top_agent
                routing['confidence'] = max(routing.get('confidence', 0.0), 0.6)
    except Exception:
        pass

    mapping = {
        'Catálogo': catalog,
        'Pedidos': pedidos,
        'Atendimento': atendimento,
        'Qualificação': qualificacao,
        'Marketing': marketing,
    }
    agent_mod = mapping.get(agente_responsavel, atendimento)

    # NOVO: contexto do Google para o agente
    contexto_google = build_context_for_intent(agente_responsavel)

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
        'info': 'Backend FastAPI: Orquestrador v2 (memória curta + viés de histórico + GoogleCtx)',
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