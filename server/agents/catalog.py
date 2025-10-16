from ..integrations.openai_client import generate_response

def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Sou o agente de Catálogo. Envio catálogo, detalhes de produtos e disponibilidade.'
    acao_especial = None

    if any(k in text for k in ['catálogo', 'catalogo', 'produto', 'produtos', 'preço', 'disponibilidade']):
        acao_especial = '[ACAO:ENVIAR_CATALOGO]'

    prev = (context or {}).get('catalog_preview') or ''
    if prev:
        prompt = (
            'Você é o agente de Catálogo da 3A Frios. Use a prévia abaixo para responder com '
            'orientação clara e objetiva. Se pedirem item específico, procure na prévia.\n\n'
            f'Catálogo (prévia):\n{prev[:1500]}'
        )
        llm = generate_response(prompt, message or '')
        if llm:
            resposta = llm
        else:
            resposta = 'Aqui está nosso catálogo atualizado e informações de produtos.'
    else:
        if acao_especial:
            resposta = 'Aqui está nosso catálogo atualizado e informações de produtos.'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }