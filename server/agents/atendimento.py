from ..integrations.openai_client import generate_response


PROMPT_ATENDIMENTO = (
    "Você é o agente de Atendimento da 3A Frios. Sua responsabilidade é tratar "
    "assuntos de suporte ao cliente: prazos de entrega, status de entrega, trocas/devoluções, "
    "atualização de endereço e orientações gerais. Responda sempre em português do Brasil, "
    "de forma breve, educada e objetiva. Peça apenas os dados mínimos necessários (ex.: CEP, "
    "número do pedido) quando for relevante. Não invente informações e, se algo não for da sua "
    "alçada (ex.: catálogo detalhado ou criação de pedido), informe que o agente correto cuidará disso."
)


def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Sou o agente de Atendimento. Ajudo com prazos, entregas, trocas e suporte.'
    acao_especial = None

    # Detecção de ações especiais (mantida independente do LLM)
    if any(k in text for k in ['endereço', 'atualizar endereço']):
        acao_especial = '[ACAO:ATUALIZAR_ENDERECO]'
    elif any(k in text for k in ['troca', 'devolução']):
        acao_especial = '[ACAO:INICIAR_TROCA_DEVOLUCAO]'
    elif any(k in text for k in ['prazo', 'entrega', 'horário']):
        pass

    identidade = (context or {}).get('identity_text') or ''
    prompt = PROMPT_ATENDIMENTO
    if identidade:
        prompt += f"\n\nContexto da empresa (Docs):\n{identidade[:1200]}"

    llm = generate_response(prompt, message or '')
    if llm:
        resposta = llm
    else:
        if acao_especial == '[ACAO:ATUALIZAR_ENDERECO]':
            resposta = 'Posso atualizar seu endereço. Me informe o novo endereço completo.'
        elif acao_especial == '[ACAO:INICIAR_TROCA_DEVOLUCAO]':
            resposta = 'Vamos iniciar o processo de troca/devolução e checar elegibilidade.'
        elif any(k in text for k in ['prazo', 'entrega', 'horário']):
            resposta = 'Entregas: normalmente 24–48h na região. Quer confirmar seu CEP?'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }