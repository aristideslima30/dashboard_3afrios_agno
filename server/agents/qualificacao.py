def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Sou o agente de Qualificação. Vou entender seu interesse e perfil.'
    acao_especial = None

    if any(k in text for k in ['qualificar', 'interesse', 'orçamento', 'perfil', 'segmento']):
        resposta = 'Vou te fazer algumas perguntas rápidas para qualificar o lead.'
        acao_especial = '[ACAO:QUALIFICAR_LEAD]'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }