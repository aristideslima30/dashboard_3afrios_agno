from ..integrations.openai_client import generate_response
from typing import List, Dict
import unicodedata


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    # remove acentos
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return s


def _pick(d: Dict[str, str], keys: List[str]) -> str:
    for k in keys:
        v = d.get(k)
        if v:
            return str(v).strip()
    return ""


def _format_item(it: Dict[str, str]) -> str:
    desc_keys = [
        'descricao', 'descrição', 'produto', 'nome', 'item', 'description'
    ]
    price_keys = ['preco', 'preço', 'valor', 'price']
    # itens vindos de fetch_sheet_catalog já têm chaves minúsculas
    desc = _pick(it, desc_keys)
    price = _pick(it, price_keys)
    if desc and price:
        return f"{desc} — R$ {price}"
    return desc or ""

def respond(message: str, context: dict | None = None):
    import logging
    logger = logging.getLogger("3afrios.backend")
    
    text = (message or '').lower()
    resposta = 'Sou o agente de Catálogo. Envio catálogo, detalhes de produtos e disponibilidade.'
    acao_especial = None
    
    logger.info(f"[Catalog] Processando mensagem: '{message}'")
    logger.info(f"[Catalog] Contexto recebido - keys: {list((context or {}).keys())}")

    # Nova detecção e resposta determinística com itens estruturados
    is_specific = any(k in text for k in ['tem', 'têm', 'teria', 'vende', 'quanto custa', 'preço de', 'valor do', 'qual valor', 'qual preço', 'qual preco'])
    is_catalog_request = any(k in text for k in ['catálogo', 'catalogo', 'produtos', 'preços', 'disponibilidade', 'lista', 'menu', 'cardápio', 'cardapio'])
    if is_catalog_request:
        acao_especial = '[ACAO:ENVIAR_CATALOGO]'

    ctx = context or {}
    items: List[Dict[str, str]] = ctx.get('catalog_items') or []
    
    logger.info(f"[Catalog] Items estruturados: {len(items)} itens")
    logger.info(f"[Catalog] is_catalog_request: {is_catalog_request}, is_specific: {is_specific}")
    
    if items:
        logger.info(f"[Catalog] USANDO RESPOSTA DETERMINÍSTICA - {len(items)} itens disponíveis")
        # tokens relevantes da mensagem para filtro simples
        raw_tokens = [t for t in _norm(message).split() if len(t) >= 3]
        stop = set(['que','qual','quais','quanto','custa','tem','têm','teria','vende','vocês','voces','vcs','de','do','da','dos','das','o','a','os','as','um','uma','me','manda','mandar','enviar','ver','lista','catalogo','catálogo','preco','preço','valor','por','kg','quilo'])
        keywords = [t for t in raw_tokens if t not in stop]

        def match(it: Dict[str, str]) -> bool:
            desc = _norm(_format_item(it))
            return any(k in desc for k in keywords) if keywords else False

        linhas: List[str] = []
        if is_specific and keywords:
            filtrados = [it for it in items if match(it)]
            if filtrados:
                for it in filtrados[:10]:
                    f = _format_item(it)
                    if f:
                        linhas.append(f)
                resposta = 'Encontrei estes itens:' + '\n' + '\n'.join(linhas)
            else:
                resposta = 'Não encontrei esse item no catálogo agora. Posso verificar a disponibilidade e retornar?'
        else:
            # pedido geral de catálogo ou apresentação
            for it in items[:12]:
                f = _format_item(it)
                if f:
                    linhas.append(f)
            if linhas:
                resposta = 'Aqui está nosso catálogo (amostra):\n' + '\n'.join(linhas)
            else:
                resposta = 'Aqui está nosso catálogo atualizado com produtos e preços.'
        
        logger.info(f"[Catalog] Resposta determinística gerada: {len(resposta)} chars")
        return {
            'resposta': resposta,
            'acao_especial': acao_especial,
        }
    
    logger.info(f"[Catalog] FALLBACK para LLM - sem itens estruturados")
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