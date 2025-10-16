def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Sou o agente de Marketing. Ajudo com campanhas, promoções e comunicação.'
    acao_especial = None

    if any(k in text for k in ['campanha', 'promoção', 'promocao', 'desconto', 'marketing', 'anúncio', 'newsletter']):
        resposta = 'Posso sugerir/ativar campanhas ou comunicar promoções vigentes.'
        acao_especial = '[ACAO:ENVIAR_CAMPANHA]'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }