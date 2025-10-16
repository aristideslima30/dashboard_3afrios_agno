from ..integrations.openai_client import generate_response

def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Sou o agente de Pedidos. Ajudo a criar e atualizar pedidos.'
    acao_especial = None

    if any(k in text for k in ['pedido', 'comprar', 'finalizar', 'ordem', 'adicionar', 'carrinho']):
        acao_especial = '[ACAO:CRIAR_OU_ATUALIZAR_PEDIDO]'

    prev = (context or {}).get('catalog_preview') or ''
    if prev:
        prompt = (
            'Você é o agente de Pedidos da 3A Frios. Quando pedirem itens, valide nomes e quantidades '
            'com base na prévia do catálogo. Se faltar informação, peça de forma objetiva.\n\n'
            f'Catálogo (prévia):\n{prev[:1200]}'
        )
        llm = generate_response(prompt, message or '')
        if llm:
            resposta = llm
        else:
            if acao_especial:
                resposta = 'Vamos criar ou atualizar seu pedido. Informe os itens e quantidades.'
    else:
        if acao_especial:
            resposta = 'Vamos criar ou atualizar seu pedido. Informe os itens e quantidades.'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }