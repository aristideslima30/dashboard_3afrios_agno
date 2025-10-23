from ..integrations.openai_client import generate_response

def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Sou o agente de Catálogo. Envio catálogo, detalhes de produtos e disponibilidade.'
    acao_especial = None

    # Detecta se é uma pergunta sobre produto específico ou catálogo geral
    is_specific = any(k in text for k in ['tem', 'possui', 'vende', 'quanto custa', 'preço de', 'valor do'])
    if any(k in text for k in ['catálogo', 'catalogo', 'produtos', 'preços', 'disponibilidade', 'lista']):
        acao_especial = '[ACAO:ENVIAR_CATALOGO]'

    prev = (context or {}).get('catalog_preview') or ''
    if prev:
        if is_specific:
            prompt = (
                'Você é o agente de Catálogo da 3A Frios. Procure no catálogo abaixo o produto específico '
                'que o cliente está perguntando. Se encontrar, informe a descrição e o preço. '
                'Se não encontrar, diga que verificará a disponibilidade.\n\n'
                f'Catálogo (produtos e preços):\n{prev[:1500]}'
            )
        else:
            prompt = (
                'Você é o agente de Catálogo da 3A Frios. Use o catálogo abaixo para apresentar '
                'nossos principais produtos e preços de forma organizada e clara.\n\n'
                f'Catálogo (produtos e preços):\n{prev[:1500]}'
            )
        
        llm = generate_response(prompt, message or '')
        if llm:
            resposta = llm
        else:
            if is_specific:
                resposta = 'Desculpe, vou verificar a disponibilidade deste produto específico e retorno em seguida.'
            else:
                resposta = 'Aqui está nosso catálogo atualizado com produtos e preços.'
    else:
        if acao_especial:
            resposta = 'Aqui está nosso catálogo atualizado com produtos e preços.'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }