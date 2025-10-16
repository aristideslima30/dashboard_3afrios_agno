def respond(message: str):
    text = (message or '').lower()
    resposta = (
        'Olá! Sou o agente de Serviço. Posso ajudar com prazos, entregas, trocas e suporte geral.'
    )
    acao_especial = None

    if 'endereço' in text or 'atualizar endereço' in text:
        resposta = (
            'Claro! Posso atualizar seu endereço. Por favor, me informe o novo endereço completo.'
        )
        acao_especial = '[ACAO:ATUALIZAR_ENDERECO]'
    elif 'catálogo' in text:
        resposta = 'Posso enviar nosso catálogo atualizado agora mesmo.'
        acao_especial = '[ACAO:ENVIAR_CATALOGO]'
    elif 'troca' in text or 'devolução' in text:
        resposta = 'Entendo que você deseja fazer uma troca. Vou orientar o processo e conferir a elegibilidade.'
    elif 'prazo' in text or 'entrega' in text or 'horário' in text:
        resposta = 'Sobre prazos e entregas: normalmente entregamos em 24–48h na região. Quer confirmar seu CEP?'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }