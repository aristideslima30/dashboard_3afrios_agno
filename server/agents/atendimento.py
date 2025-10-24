import logging
from typing import Dict, Any, List
from ..integrations.openai_client import generate_response


logger = logging.getLogger("3afrios.backend")


# Informações estruturadas da empresa
EMPRESA_INFO = {
    'nome': '3A Frios',
    'horario': {
        'seg_sex': '7h às 18h',
        'sabado': '7h às 12h', 
        'domingo': 'Fechado'
    },
    'entrega': {
        'prazo': '24-48h na região',
        'taxa_ate_3km': 'Grátis',
        'taxa_3_5km': 'R$ 3,00',
        'taxa_acima_5km': 'R$ 5,00'
    },
    'contato': {
        'whatsapp': 'Disponível durante horário comercial',
        'atendimento_humano': 'Disponível quando necessário'
    }
}

# Ana - Personalidade da assistente
ANA_PERSONALITY = {
    'nome': 'Ana',
    'cargo': 'Assistente virtual da 3A Frios',
    'tom': 'cordial, profissional e acolhedora',
    'especialidades': ['atendimento ao cliente', 'informações da empresa', 'suporte técnico']
}

# Prompts contextuais melhorados
PROMPT_BASE = f"""Você é a {ANA_PERSONALITY['nome']}, {ANA_PERSONALITY['cargo']}. 

SUA PERSONALIDADE:
- Tom: {ANA_PERSONALITY['tom']}
- Sempre se apresente como Ana da 3A Frios
- Seja empática e prestativa
- Use linguagem natural e acolhedora
- Finalize com pergunta para engajar o cliente

INFORMAÇÕES DA EMPRESA:
- Horário: {EMPRESA_INFO['horario']['seg_sex']} (Seg-Sex), {EMPRESA_INFO['horario']['sabado']} (Sáb), {EMPRESA_INFO['horario']['domingo']} (Dom)
- Entregas: {EMPRESA_INFO['entrega']['prazo']}
- Taxa entrega: {EMPRESA_INFO['entrega']['taxa_ate_3km']} até 3km, {EMPRESA_INFO['entrega']['taxa_3_5km']} (3-5km), {EMPRESA_INFO['entrega']['taxa_acima_5km']} (+5km)

SUAS RESPONSABILIDADES:
- Saudações e relacionamento com clientes
- Informações sobre horários, entregas, localização
- Suporte para trocas, devoluções, atualizações de endereço
- Tratamento de reclamações e elogios
- Encaminhamento para agentes especializados quando necessário

REGRAS IMPORTANTES:
- Se perguntarem sobre produtos/preços → encaminhe para o agente de Catálogo
- Se quiserem fazer pedidos → encaminhe para o agente de Pedidos
- Sempre seja útil e acolhedora
- Use informações reais da empresa acima"""

def detect_conversation_type(message: str, conversation_history: List[Dict[str, Any]]) -> str:
    """Detecta o tipo de conversa: primeira_interacao, conversa_ativa, retorno"""
    message_lower = message.lower()
    
    # Se não há histórico, é primeira interação
    if not conversation_history:
        return 'primeira_interacao'
    
    # Se há histórico, mas última mensagem foi há muito tempo → retorno
    # Se há histórico recente → conversa_ativa
    return 'conversa_ativa'  # Simplificado por ora

def detect_emotional_context(message: str) -> str:
    """Detecta contexto emocional da mensagem"""
    message_lower = message.lower()
    
    # Palavras positivas
    if any(word in message_lower for word in ['obrigado', 'obrigada', 'parabéns', 'excelente', 'ótimo', 'muito bom', 'adorei']):
        return 'positivo'
    
    # Palavras negativas/reclamação
    if any(word in message_lower for word in ['problema', 'reclamação', 'insatisfeito', 'ruim', 'péssimo', 'demora', 'atraso']):
        return 'negativo'
    
    # Palavras de urgência
    if any(word in message_lower for word in ['urgente', 'rápido', 'pressa', 'logo']):
        return 'urgente'
    
    return 'neutro'

def build_contextual_prompt(base_prompt: str, message: str, context: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
    """Constrói prompt contextual baseado na situação"""
    
    conv_type = detect_conversation_type(message, conversation_history)
    emotional_context = detect_emotional_context(message)
    
    # Adiciona contexto da empresa se disponível
    empresa_context = ""
    if context and context.get('identity_text'):
        empresa_context = f"\n\nContexto adicional da empresa:\n{context['identity_text'][:800]}"
    
    # Histórico resumido
    history_context = ""
    if conversation_history:
        recent_messages = conversation_history[-3:]  # Últimas 3 interações
        history_summary = []
        for msg in recent_messages:
            if msg.get('mensagem_cliente'):
                history_summary.append(f"Cliente: {msg['mensagem_cliente'][:100]}")
            if msg.get('resposta_bot'):
                history_summary.append(f"Ana: {msg['resposta_bot'][:100]}")
        
        if history_summary:
            history_context = f"\n\nContexto da conversa anterior:\n{chr(10).join(history_summary[-4:])}"
    
    # Instruções específicas baseadas no contexto
    context_instructions = ""
    
    if conv_type == 'primeira_interacao':
        context_instructions = "\n\nSITUAÇÃO: Esta é a primeira interação com este cliente. Seja especialmente acolhedora e se apresente adequadamente."
    
    if emotional_context == 'positivo':
        context_instructions += "\n\nTOM: Cliente demonstra satisfação. Seja calorosa e aproveite para fortalecer o relacionamento."
    elif emotional_context == 'negativo':
        context_instructions += "\n\nTOM: Cliente demonstra insatisfação. Seja empática, peça desculpas se necessário e foque em resolver o problema."
    elif emotional_context == 'urgente':
        context_instructions += "\n\nTOM: Cliente demonstra urgência. Seja objetiva e eficiente, priorizando soluções rápidas."
    
    return f"{base_prompt}{empresa_context}{history_context}{context_instructions}"


def respond(message: str, context: dict | None = None):
    """
    Resposta inteligente do agente Ana com contexto conversacional
    """
    text = (message or '').lower()
    acao_especial = None
    
    # Recuperar histórico da conversa do contexto
    conversation_history = []
    if context and 'conversation_history' in context:
        conversation_history = context['conversation_history']
    
    logger.info(f"[Atendimento] Ana processando mensagem: '{message[:50]}...' | Histórico: {len(conversation_history)} msgs")
    
    # === DETECÇÃO DE AÇÕES ESPECIAIS ===
    if any(k in text for k in ['endereço', 'atualizar endereço', 'mudar endereço', 'novo endereço']):
        acao_especial = '[ACAO:ATUALIZAR_ENDERECO]'
    elif any(k in text for k in ['troca', 'devolução', 'devolver', 'trocar']):
        acao_especial = '[ACAO:INICIAR_TROCA_DEVOLUCAO]'
    elif any(k in text for k in ['cancelar', 'cancelamento']):
        acao_especial = '[ACAO:CANCELAR_PEDIDO]'
    
    # === CONSTRUÇÃO DO PROMPT CONTEXTUAL ===
    prompt = build_contextual_prompt(PROMPT_BASE, message, context or {}, conversation_history)
    
    # === TENTATIVA DE RESPOSTA COM IA ===
    try:
        logger.debug(f"[Atendimento] Chamando OpenAI com prompt contextual")
        ai_response = generate_response(prompt, message or '')
        
        if ai_response and len(ai_response.strip()) > 10:
            resposta = ai_response.strip()
            logger.info(f"[Atendimento] Resposta AI gerada: {len(resposta)} chars")
            
            # Validação de qualidade da resposta
            if 'Ana' not in resposta and len(resposta) > 20:
                # Se a IA não se apresentou como Ana, ajustar
                if any(greeting in text for greeting in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
                    resposta = f"Olá! Eu sou a Ana, assistente da 3A Frios. {resposta}"
        else:
            logger.warning("[Atendimento] IA retornou resposta vazia ou muito curta")
            raise Exception("Resposta AI inadequada")
            
    except Exception as e:
        logger.error(f"[Atendimento] Erro na IA ({e}), usando fallbacks inteligentes")
        
        # === FALLBACKS INTELIGENTES BASEADOS EM CONTEXTO ===
        conv_type = detect_conversation_type(message, conversation_history)
        emotional_context = detect_emotional_context(message)
        
        # Respostas de fallback contextuais
        if acao_especial == '[ACAO:ATUALIZAR_ENDERECO]':
            resposta = 'Olá! Sou a Ana da 3A Frios. Claro, posso atualizar seu endereço! Me informe o novo endereço completo, por favor.'
        
        elif acao_especial == '[ACAO:INICIAR_TROCA_DEVOLUCAO]':
            resposta = 'Oi! Ana aqui da 3A Frios. Vou te ajudar com a troca/devolução. Me conte o que aconteceu para eu orientar o melhor processo.'
        
        elif acao_especial == '[ACAO:CANCELAR_PEDIDO]':
            resposta = 'Olá! Ana da 3A Frios aqui. Entendo que você quer cancelar o pedido. Me informe o número do pedido para eu verificar a possibilidade.'
        
        # Saudações baseadas no tipo de conversa
        elif any(greeting in text for greeting in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'ola']):
            if conv_type == 'primeira_interacao':
                resposta = 'Olá! Seja muito bem-vindo(a) à 3A Frios! 😊 Eu sou a Ana, sua assistente virtual. Estou aqui para te ajudar com informações, prazos de entrega, suporte e tudo que precisar. Como posso te ajudar hoje?'
            else:
                resposta = 'Oi! Ana da 3A Frios aqui novamente! 😊 Como posso te ajudar agora?'
        
        # Perguntas sobre horário
        elif any(k in text for k in ['horário', 'horario', 'funcionamento', 'aberto', 'fechado', 'que horas']):
            resposta = f'Oi! Ana da 3A Frios aqui! 🕒 Nossos horários são:\n\n📅 Segunda a Sexta: {EMPRESA_INFO["horario"]["seg_sex"]}\n📅 Sábado: {EMPRESA_INFO["horario"]["sabado"]}\n📅 Domingo: {EMPRESA_INFO["horario"]["domingo"]}\n\nPrecisa de mais alguma informação?'
        
        # Perguntas sobre entrega
        elif any(k in text for k in ['entrega', 'prazo', 'entregar', 'frete', 'taxa']):
            resposta = f'Oi! Ana aqui! 🚚 Sobre entregas:\n\n⏰ Prazo: {EMPRESA_INFO["entrega"]["prazo"]}\n💰 Taxa: {EMPRESA_INFO["entrega"]["taxa_ate_3km"]} até 3km, {EMPRESA_INFO["entrega"]["taxa_3_5km"]} (3-5km), {EMPRESA_INFO["entrega"]["taxa_acima_5km"]} (acima 5km)\n\nQuer que eu confirme seu CEP para calcular a taxa exata?'
        
        # Elogios/agradecimentos
        elif emotional_context == 'positivo':
            resposta = 'Que bom saber disso! 😊 Fico muito feliz em saber que você está satisfeito(a) com a 3A Frios! Nossa equipe se dedica muito para oferecer os melhores produtos e atendimento. Há mais alguma coisa em que posso te ajudar?'
        
        # Reclamações
        elif emotional_context == 'negativo':
            resposta = 'Peço desculpas pelo inconveniente! 😔 Como Ana da 3A Frios, quero resolver isso o mais rápido possível. Me conte exatamente o que aconteceu para eu encontrar a melhor solução para você.'
        
        # Perguntas sobre produtos (encaminhar)
        elif any(k in text for k in ['tem', 'produto', 'preço', 'valor', 'quanto', 'custa', 'vende', 'disponível']):
            resposta = 'Oi! Ana da 3A Frios aqui! Para informações sobre nossos produtos, preços e disponibilidade, vou te conectar com nosso especialista em catálogo que tem todas as informações atualizadas! Um momentinho... 😊'
        
        # Fallback geral
        else:
            if conv_type == 'primeira_interacao':
                resposta = 'Olá! Sou a Ana, assistente da 3A Frios! 😊 Estou aqui para te ajudar com informações sobre horários, entregas, suporte e muito mais. Como posso te ajudar hoje?'
            else:
                resposta = 'Oi! Ana da 3A Frios aqui! Como posso te ajudar? Estou disponível para informações sobre entregas, horários, suporte e orientações gerais. 😊'
    
    logger.info(f"[Atendimento] Ana finalizou resposta: {len(resposta)} chars | Ação: {acao_especial}")
    
    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }