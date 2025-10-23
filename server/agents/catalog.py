from ..integrations.openai_client import generate_response

def respond(message: str, context: dict | None = None):
    text = (message or '').lower()
    resposta = 'Aqui está nosso catálogo com produtos e preços.'
    acao_especial = None

    # Detecta se é uma pergunta sobre produto específico ou catálogo geral
    is_specific = any(k in text for k in ['tem', 'possui', 'vende', 'quanto custa', 'preço de', 'valor do'])
    is_catalog_request = any(k in text for k in ['catálogo', 'catalogo', 'produtos', 'preços', 'disponibilidade', 'lista'])
    if is_catalog_request:
        acao_especial = '[ACAO:ENVIAR_CATALOGO]'

    prev = (context or {}).get('catalog_preview') or ''
    preview_lines = [l for l in (prev.splitlines() if prev else []) if l.strip()]

    if prev:
        # Para pedidos explícitos de catálogo, prioriza mostrar um recorte do preview
        if is_catalog_request and preview_lines:
            snippet = '\n'.join(preview_lines[:12])
            resposta = f"Aqui está nosso catálogo atualizado com produtos e preços:\n{snippet}"
        else:
            if is_specific:
                # Tenta encontrar linhas do preview que batem com palavras da pergunta
                tokens = [t.strip() for t in text.replace('\n', ' ').split(' ') if len(t.strip()) >= 3]
                matches = []
                for line in preview_lines:
                    lt = line.lower()
                    if any(tok in lt for tok in tokens):
                        matches.append(line)
                    if len(matches) >= 6:
                        break
                if matches:
                    resposta = 'Encontrei estes itens relacionados:\n' + '\n'.join(matches)
                else:
                    # Usa LLM para tentar localizar/explicar
                    prompt = (
                        'Você é o agente de Catálogo da 3A Frios. Procure no catálogo abaixo o produto específico '
                        'que o cliente está perguntando. Se encontrar, informe a descrição e o preço. '
                        'Se não encontrar, diga que verificará a disponibilidade.\n\n'
                        f'Catálogo (produtos e preços):\n{prev[:1500]}'
                    )
                    llm = generate_response(prompt, message or '')
                    if llm:
                        resposta = llm
                    else:
                        resposta = 'Desculpe, vou verificar a disponibilidade deste produto específico e retorno em seguida.'
            else:
                # Apresentação geral usando LLM com fallback para preview
                prompt = (
                    'Você é o agente de Catálogo da 3A Frios. Use o catálogo abaixo para apresentar '
                    'nossos principais produtos e preços de forma organizada e clara.\n\n'
                    f'Catálogo (produtos e preços):\n{prev[:1500]}'
                )
                llm = generate_response(prompt, message or '')
                if llm:
                    resposta = llm
                else:
                    snippet = '\n'.join(preview_lines[:12]) if preview_lines else ''
                    resposta = 'Aqui está nosso catálogo atualizado com produtos e preços.' + (f"\n{snippet}" if snippet else '')
    else:
        # Sem preview: responde e aciona envio de catálogo quando solicitado
        if is_catalog_request:
            resposta = 'Aqui está nosso catálogo atualizado com produtos e preços.'
            acao_especial = acao_especial or '[ACAO:ENVIAR_CATALOGO]'
        elif is_specific:
            resposta = 'Desculpe, vou verificar a disponibilidade deste produto específico e retorno em seguida.'
        else:
            resposta = 'No momento não consegui acessar o catálogo. Posso enviar a lista completa em seguida.'

    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }