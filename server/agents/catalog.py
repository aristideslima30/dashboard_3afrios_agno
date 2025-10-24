from ..integrations.openai_client import generate_response
from typing import List, Dict, Any
import unicodedata
import logging

# Sofia - Especialista em Catálogo
SOFIA_PERSONALITY = {
    'nome': 'Sofia',
    'cargo': 'Especialista em produtos da 3A Frios',
    'tom': 'conhecedora, prestativa e comercial',
    'especialidades': ['produtos', 'preços', 'sugestões comerciais', 'combos']
}

# Dicas comerciais inteligentes
DICAS_COMERCIAIS = {
    'quantidades_praticas': {
        'casal': '500g é ideal para vocês dois',
        'familia_pequena': '1kg é perfeito para uma família pequena',
        'familia_grande': '2kg rende bem para a família toda',
        'churrasquinho': '1,5kg é ideal para um churrasquinho'
    },
    'combos_populares': {
        'churrasco': ['picanha', 'linguiça', 'frango'],
        'frios_lanche': ['presunto', 'queijo', 'mortadela'],
        'carne_semana': ['contrafilé', 'alcatra', 'patinho']
    },
    'produtos_complementares': {
        'picanha': ['sal grosso', 'linguiça', 'frango'],
        'queijo': ['presunto', 'mortadela', 'copa'],
        'frango': ['linguiça', 'sal tempero', 'batata']
    }
}

logger = logging.getLogger("3afrios.backend")


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


def _format_item(it: Dict[str, str], style: str = 'basic') -> str:
    """Formata produto com diferentes estilos de apresentação"""
    desc_keys = [
        'descricao', 'descrição', 'produto', 'nome', 'item', 'description'
    ]
    price_keys = ['preco', 'preço', 'valor', 'price']
    # itens vindos de fetch_sheet_catalog já têm chaves minúsculas
    desc = _pick(it, desc_keys)
    price = _pick(it, price_keys)
    
    if not desc:
        return ""
    
    if style == 'basic':
        if desc and price:
            return f"🥩 {desc} — R$ {price}"
        return f"🥩 {desc}"
    
    elif style == 'detailed':
        if desc and price:
            # Adiciona emoji específico baseado no tipo de produto
            emoji = _get_product_emoji(desc)
            return f"{emoji} **{desc}** — R$ {price}/kg"
        return f"🥩 {desc}"
    
    elif style == 'commercial':
        if desc and price:
            emoji = _get_product_emoji(desc)
            return f"{emoji} {desc}\n   💰 R$ {price}/kg"
        return f"🥩 {desc}"
    
    return desc or ""

def _get_product_emoji(desc: str) -> str:
    """Retorna emoji apropriado baseado no tipo de produto"""
    desc_lower = desc.lower()
    
    if any(word in desc_lower for word in ['boi', 'picanha', 'alcatra', 'contrafilé', 'maminha']):
        return '🥩'  # Carne bovina
    elif any(word in desc_lower for word in ['porco', 'pernil', 'costela', 'lombo']):
        return '🐷'  # Carne suína
    elif any(word in desc_lower for word in ['frango', 'coxa', 'peito', 'asa']):
        return '🐔'  # Frango
    elif any(word in desc_lower for word in ['linguiça', 'calabresa', 'salsicha']):
        return '🌭'  # Embutidos
    elif any(word in desc_lower for word in ['queijo', 'presunto', 'mortadela']):
        return '🧀'  # Frios
    elif any(word in desc_lower for word in ['peixe', 'salmão', 'tilápia']):
        return '🐟'  # Peixes
    else:
        return '🥩'  # Default


def _get_product_keywords(message: str) -> List[str]:
    """Extrai palavras-chave expandidas com sinônimos e categorias"""
    # Remove pontuação e normaliza
    clean_msg = _norm(message.replace('?', '').replace('!', '').replace('.', '').replace(',', ''))
    raw_tokens = [t for t in clean_msg.split() if len(t) >= 3]
    stop = set(['que','qual','quais','quanto','custa','tem','têm','teria','vende','vocês','voces','vcs','de','do','da','dos','das','o','a','os','as','um','uma','me','manda','mandar','enviar','ver','lista','catalogo','catálogo','preco','preço','valor','por','kg','quilo'])
    keywords = [t for t in raw_tokens if t not in stop]
    
    # Expande com sinônimos e categorias
    expanded = set(keywords)
    
    # Mapeamento de categorias
    categorias = {
        'porco': ['calabresa', 'linguica', 'linguiça', 'pernil', 'costela', 'lombo', 'bacon'],
        'suino': ['calabresa', 'linguica', 'linguiça', 'pernil', 'costela', 'lombo', 'bacon'],
        'suína': ['calabresa', 'linguica', 'linguiça', 'pernil', 'costela', 'lombo', 'bacon'],
        'gado': ['picanha', 'alcatra', 'maminha', 'contrafile', 'coxao', 'patinho', 'acem'],
        'bovino': ['picanha', 'alcatra', 'maminha', 'contrafile', 'coxao', 'patinho', 'acem'],
        'boi': ['picanha', 'alcatra', 'maminha', 'contrafile', 'coxao', 'patinho', 'acem'],
        'frango': ['coxa', 'sobrecoxa', 'peito', 'asa', 'coxinha', 'filezinho'],
        'aves': ['coxa', 'sobrecoxa', 'peito', 'asa', 'coxinha', 'filezinho', 'frango'],
        'frios': ['mortadela', 'presunto', 'queijo', 'salamie', 'copa'],
        'embutidos': ['calabresa', 'linguica', 'linguiça', 'salsicha', 'mortadela']
    }
    
    # Adiciona produtos da categoria se palavra for categoria
    for palavra in list(keywords):  # usa lista para não modificar durante iteração
        if palavra in categorias:
            expanded.update(categorias[palavra])
    
    return list(expanded)


def _match_product(item: Dict[str, str], keywords: List[str]) -> bool:
    """Verifica se um produto match com as palavras-chave expandidas"""
    desc = _norm(_format_item(item))
    return any(k in desc for k in keywords) if keywords else False

def _suggest_quantity(product_name: str, context: str = "") -> str:
    """Sugere quantidade prática baseada no produto e contexto"""
    product_lower = product_name.lower()
    
    # Produtos que vendem bem em quantidade maior
    if any(word in product_lower for word in ['picanha', 'alcatra', 'contrafilé']):
        return "Sugestão: 1kg é ideal para 4-5 pessoas 👨‍👩‍👧‍👦"
    
    # Produtos para lanche/frios
    elif any(word in product_lower for word in ['presunto', 'queijo', 'mortadela']):
        return "Sugestão: 300-500g é perfeito para lanches da semana 🥪"
    
    # Embutidos
    elif any(word in product_lower for word in ['linguiça', 'calabresa']):
        return "Sugestão: 500g acompanha bem um churrasco 🔥"
    
    # Frango
    elif any(word in product_lower for word in ['frango', 'coxa', 'peito']):
        return "Sugestão: 1kg alimenta bem a família 🏠"
    
    return "Sugestão: Fale comigo para calcularmos a quantidade ideal! 😊"

def _suggest_combo(main_product: str, available_items: List[Dict[str, str]]) -> List[str]:
    """Sugere produtos complementares baseado no produto principal"""
    main_lower = main_product.lower()
    suggestions = []
    
    # Busca produtos complementares nos itens disponíveis
    if any(word in main_lower for word in ['picanha', 'alcatra']):
        # Para carnes nobis, sugere linguiça e sal
        for item in available_items:
            desc = _norm(_format_item(item))
            if any(word in desc for word in ['linguiça', 'calabresa', 'sal']):
                suggestions.append(_format_item(item, 'basic'))
    
    elif any(word in main_lower for word in ['queijo']):
        # Para queijo, sugere presunto
        for item in available_items:
            desc = _norm(_format_item(item))
            if any(word in desc for word in ['presunto', 'mortadela']):
                suggestions.append(_format_item(item, 'basic'))
    
    elif any(word in main_lower for word in ['frango']):
        # Para frango, sugere linguiça
        for item in available_items:
            desc = _norm(_format_item(item))
            if any(word in desc for word in ['linguiça', 'sal', 'tempero']):
                suggestions.append(_format_item(item, 'basic'))
    
    return suggestions[:3]  # Máximo 3 sugestões

def _build_commercial_response(produtos: List[Dict[str, str]], query: str, total_count: int) -> str:
    """Constrói resposta comercial inteligente"""
    if not produtos:
        return _build_not_found_response(query)
    
    # Cabeçalho personalizado
    if total_count == 1:
        header = f"Encontrei o produto que você procura! 🎯"
    else:
        header = f"Encontrei {len(produtos)} opções para você! 😊"
    
    # Lista produtos com formatação comercial
    linhas = []
    for produto in produtos:
        linha = _format_item(produto, 'commercial')
        if linha:
            linhas.append(linha)
            
            # Adiciona sugestão de quantidade para o primeiro produto
            if len(linhas) == 1:
                desc = _pick(produto, ['descricao', 'descrição', 'produto', 'nome'])
                sugestao_qtd = _suggest_quantity(desc)
                linhas.append(f"   💡 {sugestao_qtd}")
    
    produtos_text = '\n'.join(linhas)
    
    # Sugestões comerciais
    if produtos:
        primeiro_produto = _pick(produtos[0], ['descricao', 'descrição', 'produto', 'nome'])
        combos = _suggest_combo(primeiro_produto, produtos)
        
        combo_text = ""
        if combos:
            combo_text = f"\n\n🔥 **Combina bem com:**\n" + '\n'.join(combos)
        
        # Call to action
        cta = f"\n\n💬 Quer fazer o pedido ou tem alguma dúvida? Estou aqui para te ajudar!"
        
        return f"{header}\n\n{produtos_text}{combo_text}{cta}"
    
    return f"{header}\n\n{produtos_text}"

def _build_not_found_response(query: str) -> str:
    """Constrói resposta quando produto não é encontrado"""
    return f"""Não encontrei especificamente "{query}" no catálogo agora, mas posso te ajudar! 🤔

🔍 **Opções:**
• Posso verificar se temos produtos similares
• Consultar disponibilidade com fornecedores  
• Enviar o catálogo completo para você escolher

💬 Me conte: que tipo de carne/produto você está procurando? Vou encontrar a melhor opção para você! 😊"""


def respond(message: str, context: dict | None = None):
    """
    Sofia - Especialista em produtos da 3A Frios
    Resposta inteligente com sugestões comerciais e personalidade
    """
    text = (message or '').lower()
    acao_especial = None
    
    logger.info(f"[Catalog] Sofia processando: '{message[:50]}...'")
    logger.info(f"[Catalog] Contexto recebido - keys: {list((context or {}).keys())}")
    
    # Recuperar histórico da conversa do contexto
    conversation_history = []
    if context and 'conversation_history' in context:
        conversation_history = context['conversation_history']

    # === DETECÇÃO DE TIPOS DE CONSULTA ===
    is_specific = any(k in text for k in ['tem', 'têm', 'teria', 'vende', 'quanto custa', 'preço de', 'valor do', 'qual valor', 'qual preço', 'qual preco'])
    is_catalog_request = any(k in text for k in ['catálogo', 'catalogo', 'produtos', 'preços', 'disponibilidade', 'lista', 'menu', 'cardápio', 'cardapio'])
    is_greeting = any(k in text for k in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite'])
    
    if is_catalog_request:
        acao_especial = '[ACAO:ENVIAR_CATALOGO]'

    ctx = context or {}
    items: List[Dict[str, str]] = ctx.get('catalog_items') or []
    
    logger.info(f"[Catalog] Sofia analisou: {len(items)} itens | específica: {is_specific} | catálogo: {is_catalog_request}")
    
    # === RESPOSTA COM PRODUTOS ESTRUTURADOS ===
    if items:
        logger.info(f"[Catalog] Sofia usando catálogo real - {len(items)} produtos disponíveis")
        
        # Saudação específica da Sofia
        if is_greeting and not is_specific and not is_catalog_request:
            conv_type = "primeira_interacao" if not conversation_history else "conversa_ativa"
            if conv_type == "primeira_interacao":
                resposta = f"Oi! Eu sou a Sofia, especialista em produtos da 3A Frios! 😊🥩\n\nEstou aqui para te ajudar a encontrar os melhores produtos com os melhores preços. Temos carnes, frios, embutidos e muito mais!\n\nO que você está procurando hoje?"
            else:
                resposta = f"Oi! Sofia aqui novamente! 😊 Como posso te ajudar com nossos produtos?"
            
            return {
                'resposta': resposta,
                'acao_especial': acao_especial,
            }
        
        # Busca específica por produtos
        if is_specific:
            keywords = _get_product_keywords(message)
            logger.info(f"[Catalog] Sofia buscando por: {keywords}")

            if keywords:
                filtrados = [it for it in items if _match_product(it, keywords)]
                if filtrados:
                    # Resposta comercial inteligente
                    resposta = _build_commercial_response(filtrados, ' '.join(keywords), len(filtrados))
                else:
                    # Produto não encontrado
                    resposta = _build_not_found_response(' '.join(keywords))
            else:
                resposta = "Oi! Sou a Sofia da 3A Frios! 😊 Me conta que produto você está procurando que eu te ajudo a encontrar!"
        
        # Pedido geral de catálogo  
        else:
            # Apresenta catálogo com toque comercial da Sofia
            linhas = []
            for it in items[:8]:  # Menos produtos, mais foco
                f = _format_item(it, 'commercial')
                if f:
                    linhas.append(f)
            
            if linhas:
                produtos_text = '\n'.join(linhas)
                resposta = f"""Oi! Sofia aqui da 3A Frios! 😊🥩

Aqui estão alguns dos nossos **produtos em destaque**:

{produtos_text}

💡 **Dica da Sofia:** Precisa de sugestões de quantidade ou quer montar um combo? Me fala o que você tem em mente que eu personalizo para você!

📱 O que mais posso te ajudar?"""
            else:
                resposta = "Oi! Sofia da 3A Frios aqui! 😊 Nosso catálogo está atualizando, mas posso te ajudar com qualquer produto! Me conta o que você precisa!"
        
        logger.info(f"[Catalog] Sofia finalizou resposta comercial: {len(resposta)} chars")
        return {
            'resposta': resposta,
            'acao_especial': acao_especial,
        }
    
    # === FALLBACK INTELIGENTE DA SOFIA ===
    logger.info(f"[Catalog] Sofia usando fallback inteligente - sem itens estruturados")
    
    prev = (context or {}).get('catalog_preview') or ''
    if prev:
        # Prompt personalizado da Sofia
        base_prompt = f"""Você é a Sofia, especialista em produtos da 3A Frios. 

PERSONALIDADE:
- Nome: Sofia, especialista em produtos
- Tom: prestativa, conhecedora e comercial
- Sempre se apresente como Sofia da 3A Frios
- Use emojis relacionados a produtos (🥩🐔🧀🌭)
- Sugira quantidades práticas e produtos complementares
- Seja comercial mas não agressiva

SUA MISSÃO:
- Ajudar clientes a encontrar os melhores produtos
- Sugerir quantidades ideais baseadas na necessidade
- Oferecer combos e produtos complementares
- Educar sobre qualidade dos produtos

CATÁLOGO DISPONÍVEL:
{prev[:1200]}"""

        if is_specific:
            prompt = f"""{base_prompt}

SITUAÇÃO: Cliente perguntando por produto específico.
INSTRUÇÃO: Procure o produto no catálogo. Se encontrar, apresente com preço e sugira quantidade. Se não encontrar, ofereça alternativas similares e se disponha a verificar disponibilidade."""

        else:
            prompt = f"""{base_prompt}

SITUAÇÃO: Cliente quer ver o catálogo geral.
INSTRUÇÃO: Apresente os principais produtos de forma organizada e atrativa, com dicas comerciais."""

        try:
            ai_response = generate_response(prompt, message or '')
            if ai_response and len(ai_response.strip()) > 10:
                resposta = ai_response.strip()
                
                # Garante que Sofia se apresentou
                if 'Sofia' not in resposta:
                    if is_greeting:
                        resposta = f"Oi! Eu sou a Sofia da 3A Frios! 😊🥩 {resposta}"
                    
                logger.info(f"[Catalog] Sofia (AI) gerou resposta: {len(resposta)} chars")
            else:
                raise Exception("Resposta AI inadequada")
                
        except Exception as e:
            logger.error(f"[Catalog] Sofia fallback para respostas determinísticas: {e}")
            
            # Fallbacks determinísticos da Sofia
            if is_greeting:
                resposta = "Oi! Eu sou a Sofia, especialista em produtos da 3A Frios! 😊🥩\n\nEstou aqui para te ajudar a encontrar os melhores produtos com ótimos preços. O que você está procurando hoje?"
            elif is_specific:
                resposta = "Oi! Sofia da 3A Frios aqui! 😊 Vou verificar esse produto específico para você e já retorno com preço e disponibilidade!"
            elif is_catalog_request:
                resposta = "Oi! Sofia aqui! 😊 Vou te enviar nosso catálogo completo com todos os produtos e preços atualizados!"
            else:
                resposta = "Oi! Sou a Sofia da 3A Frios! 😊🥩 Sou especialista em produtos e estou aqui para te ajudar. Me conta o que você precisa!"
    
    else:
        # Sem contexto algum
        if is_greeting:
            resposta = "Oi! Eu sou a Sofia da 3A Frios! 😊🥩 Especialista em produtos e preços. Como posso te ajudar hoje?"
        elif is_catalog_request:
            resposta = "Oi! Sofia aqui! 😊 Vou providenciar nosso catálogo atualizado para você!"
        else:
            resposta = "Oi! Sofia da 3A Frios! 😊 Me conta que produto você está procurando que eu te ajudo!"

    logger.info(f"[Catalog] Sofia finalizou: {len(resposta)} chars | Ação: {acao_especial}")
    
    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }