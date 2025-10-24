from ..integrations.openai_client import generate_response
import logging
from typing import Dict, List, Any
import re

logger = logging.getLogger(__name__)

# === PERSONALIDADE E CONFIGURAÇÕES DO BRUNO ===

BRUNO_PERSONALITY = {
    'nome': 'Bruno',
    'cargo': 'Especialista em Qualificação de Leads da 3A Frios',
    'personalidade': [
        'Curioso e investigativo',
        'Amigável mas focado em resultados',
        'Habilidoso em fazer perguntas certas',
        'Entende necessidades rapidamente',
        'Conecta pessoas aos produtos ideais'
    ],
    'tom': 'consultivo e descoberta',
    'emojis': ['🎯', '🔍', '💡', '📊', '✨', '🎪', '🤝', '📋']
}

SEGMENTOS_CLIENTE = {
    'pessoa_fisica': {
        'indicadores': ['família', 'casa', 'churrasco', 'final de semana', 'aniversário', 'festa'],
        'abordagem': 'familiar e acolhedora',
        'perguntas_foco': ['ocasião', 'quantidade_pessoas', 'preferencias', 'frequencia']
    },
    'pessoa_juridica': {
        'indicadores': ['empresa', 'restaurante', 'evento', 'corporativo', 'cnpj', 'buffet'],
        'abordagem': 'profissional e eficiente',
        'perguntas_foco': ['volume', 'regularidade', 'prazo', 'orcamento', 'especificacoes']
    },
    'especial': {
        'indicadores': ['casamento', 'formatura', 'aniversário', 'confraternização'],
        'abordagem': 'consultiva e detalhista',
        'perguntas_foco': ['data', 'convidados', 'estilo', 'orcamento', 'servico_completo']
    }
}

TIPOS_NECESSIDADE = {
    'descoberta': ['primeira vez', 'não sei', 'me ajuda', 'recomenda', 'sugestão'],
    'urgente': ['hoje', 'amanhã', 'urgente', 'rápido', 'preciso logo'],
    'planejada': ['próxima semana', 'mês que vem', 'estou planejando', 'organizando'],
    'comparacao': ['preço', 'comparar', 'melhor opção', 'diferença', 'orçamento']
}

class PerfilCliente:
    DESCOBERTA = "descoberta"
    QUALIFICADO = "qualificado"
    PRONTO_COMPRA = "pronto_compra"
    NECESSITA_NUTRICAO = "necessita_nutricao"

def _detect_client_segment(message: str) -> str:
    """Detecta segmento do cliente baseado na mensagem"""
    text = message.lower()
    
    # Pontuação para cada segmento
    scores = {'pessoa_fisica': 0, 'pessoa_juridica': 0, 'especial': 0}
    
    for segmento, config in SEGMENTOS_CLIENTE.items():
        for indicador in config['indicadores']:
            if indicador in text:
                scores[segmento] += 1
    
    # Retorna segmento com maior pontuação ou 'pessoa_fisica' como padrão
    return max(scores.items(), key=lambda x: x[1])[0] if max(scores.values()) > 0 else 'pessoa_fisica'

def _detect_need_type(message: str) -> List[str]:
    """Detecta tipos de necessidade na mensagem"""
    text = message.lower()
    detected_types = []
    
    for tipo, indicadores in TIPOS_NECESSIDADE.items():
        for indicador in indicadores:
            if indicador in text:
                detected_types.append(tipo)
                break
    
    return detected_types or ['descoberta']

def _extract_context_clues(message: str) -> Dict[str, Any]:
    """Extrai pistas de contexto da mensagem"""
    text = message.lower()
    clues = {}
    
    # Detecta quantidade de pessoas
    pessoas_patterns = [
        r'(\d+)\s*pessoas?',
        r'para\s+(\d+)',
        r'somos\s+(\d+)',
        r'família\s+de\s+(\d+)'
    ]
    
    for pattern in pessoas_patterns:
        match = re.search(pattern, text)
        if match:
            clues['quantidade_pessoas'] = int(match.group(1))
            break
    
    # Detecta urgência temporal
    urgencia_patterns = [
        r'hoje|amanhã|urgente',
        r'esta\s+semana|essa\s+semana',
        r'próxima\s+semana|semana\s+que\s+vem',
        r'mês\s+que\s+vem|próximo\s+mês'
    ]
    
    for i, pattern in enumerate(urgencia_patterns):
        if re.search(pattern, text):
            clues['urgencia'] = ['alta', 'media', 'baixa', 'planejada'][i]
            break
    
    # Detecta orçamento mencionado
    orcamento_pattern = r'r?\$?\s*(\d+(?:[\.,]\d+)?)'
    matches = re.findall(orcamento_pattern, text)
    if matches:
        try:
            clues['orcamento_mencionado'] = float(matches[0].replace(',', '.'))
        except ValueError:
            pass
    
    return clues

def _generate_qualification_questions(segmento: str, need_types: List[str], context_clues: Dict) -> List[str]:
    """Gera perguntas de qualificação baseadas no perfil detectado"""
    questions = []
    
    config = SEGMENTOS_CLIENTE[segmento]
    
    # Perguntas baseadas no segmento
    if segmento == 'pessoa_fisica':
        if 'quantidade_pessoas' not in context_clues:
            questions.append("Para quantas pessoas você está planejando?")
        if 'descoberta' in need_types:
            questions.append("Que tipo de ocasião você está organizando?")
        questions.append("Vocês têm alguma preferência de corte ou já sabem o que querem?")
        
    elif segmento == 'pessoa_juridica':
        questions.append("Qual o volume aproximado que vocês trabalham?")
        questions.append("É uma demanda regular ou pontual?")
        if 'orcamento_mencionado' not in context_clues:
            questions.append("Qual a faixa de investimento que vocês estão considerando?")
            
    elif segmento == 'especial':
        if 'quantidade_pessoas' not in context_clues:
            questions.append("Quantos convidados vocês esperam?")
        questions.append("Já têm uma data definida?")
        questions.append("Vocês querem só as carnes ou um serviço mais completo?")
    
    # Perguntas baseadas no tipo de necessidade
    if 'urgente' in need_types and 'urgencia' not in context_clues:
        questions.append("Para quando vocês precisam?")
    elif 'comparacao' in need_types:
        questions.append("Vocês já viram opções em outros lugares?")
        
    return questions[:3]  # Máximo 3 perguntas por interação

def respond(message: str, context: dict | None = None):
    """
    Bruno - Especialista em Qualificação de Leads da 3A Frios
    Descobre necessidades e qualifica clientes de forma inteligente
    """
    text = (message or '').lower()
    acao_especial = None
    
    logger.info(f"[Qualificação] Bruno processando: '{message[:50]}...'")
    
    # Recuperar contexto
    conversation_history = context.get('conversation_history', []) if context else []
    catalog_items = context.get('catalog_items', []) if context else []
    
    logger.info(f"[Qualificação] Bruno analisando lead")
    
    # === ANÁLISE INTELIGENTE DO CLIENTE ===
    segmento = _detect_client_segment(message)
    need_types = _detect_need_type(message)
    context_clues = _extract_context_clues(message)
    
    logger.info(f"[Qualificação] Segmento: {segmento}, Necessidades: {need_types}")
    
    # === DETECÇÃO DE TIPOS DE INTERAÇÃO ===
    is_greeting = any(k in text for k in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite'])
    is_qualification_request = any(k in text for k in ['qualificar', 'interesse', 'orçamento', 'perfil', 'segmento'])
    is_providing_info = any(k in text for k in ['somos', 'precisamos', 'queremos', 'para', 'evento', 'festa'])
    is_asking_questions = any(k in text for k in ['quanto', 'como', 'qual', 'onde', 'quando'])
    
    # === LÓGICA PRINCIPAL DO BRUNO ===
    
    # Saudação inicial com análise de contexto
    if is_greeting and not is_providing_info:
        resposta = f"""Oi! Eu sou o Bruno, especialista em qualificação da 3A Frios! 🎯✨

Minha missão é entender exatamente o que você precisa para te conectar com as melhores soluções!

🔍 Sou especialista em:
• Descobrir suas necessidades específicas
• Qualificar o perfil ideal de produtos  
• Conectar você com nossos especialistas certos
• Garantir que você tenha a melhor experiência

💡 Me conta: o que está planejando? Estou aqui para descobrir a solução perfeita para você!"""
        
        return {'resposta': resposta, 'acao_especial': acao_especial}
    
    # Cliente fornecendo informações - processo de qualificação
    if is_providing_info or is_qualification_request:
        acao_especial = '[ACAO:QUALIFICAR_LEAD]'
        
        # Gera perguntas de qualificação
        questions = _generate_qualification_questions(segmento, need_types, context_clues)
        
        # Análise do perfil
        config = SEGMENTOS_CLIENTE[segmento]
        
        if context_clues:
            # Cliente forneceu informações úteis
            resposta = f"""Perfeito! Bruno aqui analisando seu perfil! 🔍✨

Entendi que você está planejando algo especial! Deixe-me qualificar melhor para te ajudar:

"""
            if 'quantidade_pessoas' in context_clues:
                resposta += f"👥 Para {context_clues['quantidade_pessoas']} pessoas - ótimo!\n"
            
            if 'urgencia' in context_clues:
                urgencia_msg = {
                    'alta': '⚡ Urgência alta - vamos priorizar sua demanda!',
                    'media': '📅 Para esta semana - conseguimos organizar!',
                    'baixa': '🗓️ Prazo confortável - podemos planejar bem!',
                    'planejada': '📋 Planejamento antecipado - excelente!'
                }
                resposta += urgencia_msg.get(context_clues['urgencia'], '') + '\n'
            
            resposta += f"\n🎯 **Algumas perguntas para qualificar melhor:**\n"
            for i, question in enumerate(questions, 1):
                resposta += f"{i}. {question}\n"
                
            resposta += f"\n💡 Com essas informações vou te conectar com o especialista ideal da nossa equipe!"
        
        else:
            # Primeira interação de qualificação
            resposta = f"""Oi! Bruno da 3A Frios aqui! 🎯🔍

Que ótimo que você está interessado! Vou fazer algumas perguntas estratégicas para entender exatamente o que você precisa:

"""
            for i, question in enumerate(questions, 1):
                resposta += f"{i}. {question}\n"
                
            resposta += f"""
✨ **Por que essas perguntas?**
Cada cliente tem necessidades únicas, e eu quero garantir que você seja direcionado para o especialista certo com a proposta perfeita!

🎪 Me conta mais que vou qualificar seu perfil para a melhor experiência!"""
    
    # Cliente fazendo perguntas - modo consultivo
    elif is_asking_questions:
        # Usa IA para resposta consultiva baseada no segmento
        if catalog_items:
            catalog_preview = "\n".join([
                f"• {item.get('descricao', item.get('produto', ''))} - R$ {item.get('preco', 'N/A')}"
                for item in catalog_items[:6]
            ])
            
            prompt = f"""Você é o Bruno, especialista em qualificação de leads da 3A Frios.

PERSONALIDADE:
- Nome: Bruno, especialista em qualificação
- Tom: curioso, consultivo e focado em descoberta
- Sempre se apresente como Bruno da 3A Frios
- Use emojis relacionados à descoberta (🎯🔍💡📊)
- Faça perguntas estratégicas para qualificar
- Conecte necessidades aos produtos certos

SEGMENTO DETECTADO: {segmento}
NECESSIDADES IDENTIFICADAS: {', '.join(need_types)}

PRODUTOS DISPONÍVEIS:
{catalog_preview}

INSTRUÇÃO: Responda de forma consultiva, qualificando a necessidade e direcionando para o próximo passo."""

            try:
                ai_response = generate_response(prompt, message or '')
                if ai_response and len(ai_response.strip()) > 10:
                    resposta = ai_response.strip()
                    
                    # Garante que Bruno se apresentou
                    if 'Bruno' not in resposta:
                        resposta = f"Oi! Bruno da 3A Frios aqui! 🎯🔍 {resposta}"
                else:
                    raise Exception("Resposta AI inadequada")
                    
            except Exception as e:
                logger.error(f"[Qualificação] Bruno fallback: {e}")
                resposta = f"""Oi! Bruno da 3A Frios! 🎯🔍

Excelente pergunta! Para te dar a resposta mais precisa, preciso entender melhor seu perfil:

• Que tipo de evento você está organizando?
• Para quantas pessoas?
• Qual o prazo que você tem?

💡 Com essas informações vou te dar uma orientação muito mais assertiva!"""
        
        else:
            resposta = f"""Oi! Bruno da 3A Frios! 🎯🔍

Ótima pergunta! Para te dar a melhor orientação, me conta um pouco mais sobre o que você está planejando:

• Qual a ocasião?
• Para quantas pessoas?
• Que tipo de produto você tem em mente?

🎪 Quanto mais eu souber, melhor vou conseguir te qualificar e direcionar!"""
    
    # Fallback inteligente do Bruno
    else:
        try:
            # Usa IA para casos complexos
            prompt = f"""Você é o Bruno, especialista em qualificação de leads da 3A Frios.

PERSONALIDADE:
- Nome: Bruno, especialista em qualificação
- Tom: curioso, consultivo e investigativo
- Sempre se apresente como Bruno da 3A Frios  
- Use emojis relacionados à descoberta (🎯🔍💡📊✨)
- Sua missão é descobrir necessidades e qualificar clientes
- Faça perguntas estratégicas para entender o perfil

OBJETIVO: Qualificar o lead descobrindo necessidades, perfil e direcionando para os especialistas certos.

INSTRUÇÃO: Responda de forma consultiva, fazendo perguntas para qualificar o cliente."""

            ai_response = generate_response(prompt, message or '')
            if ai_response and len(ai_response.strip()) > 10:
                resposta = ai_response.strip()
                
                if 'Bruno' not in resposta:
                    resposta = f"Oi! Bruno da 3A Frios aqui! 🎯 {resposta}"
            else:
                raise Exception("Resposta AI inadequada")
                
        except Exception as e:
            logger.error(f"[Qualificação] Bruno fallback: {e}")
            resposta = f"Oi! Bruno da 3A Frios! 🎯🔍 Especialista em qualificação aqui! Me conta o que você está planejando que vou descobrir a solução perfeita para você!"
    
    logger.info(f"[Qualificação] Bruno finalizou: {len(resposta)} chars | Ação: {acao_especial}")
    
    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }