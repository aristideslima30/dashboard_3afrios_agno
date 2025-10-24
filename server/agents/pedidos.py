from ..integrations.openai_client import generate_response
from .service import get_service_utils
from typing import List, Dict, Any, Tuple
import logging
import re
import unicodedata

# Roberto - Especialista em Pedidos
ROBERTO_PERSONALITY = {
    'nome': 'Roberto',
    'cargo': 'Especialista em pedidos da 3A Frios',
    'tom': 'eficiente, atencioso e organizador',
    'especialidades': ['gestão de pedidos', 'cálculos', 'logística', 'confirmações']
}

# Informações do sistema de delivery
DELIVERY_INFO = {
    'formas_pagamento': [
        'Dinheiro na entrega',
        'Cartão de crédito na entrega', 
        'PIX',
        'Transferência bancária'
    ],
    'taxa_entrega': {
        'ate_3km': 'Grátis',
        '3_5km': 'R$ 3,00',
        'acima_5km': 'R$ 5,00'
    },
    'prazo_entrega': '24-48h na região',
    'horario_pedidos': 'Segunda a Sexta: 7h às 18h | Sábado: 7h às 12h'
}

# Estados do processo de pedido
class EstadoPedido:
    INICIANDO = "iniciando"
    COLETANDO_ITENS = "coletando_itens"
    VALIDANDO_PRODUTOS = "validando_produtos"
    CALCULANDO_TOTAL = "calculando_total"
    COLETANDO_ENDERECO = "coletando_endereco"
    ESCOLHENDO_PAGAMENTO = "escolhendo_pagamento"
    CONFIRMANDO = "confirmando"
    FINALIZADO = "finalizado"

logger = logging.getLogger("3afrios.backend")

def _norm(s: str) -> str:
    """Normaliza string removendo acentos e convertendo para minúsculas"""
    s = (s or "").strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return s

def _extract_items_from_message(message: str) -> List[Dict[str, Any]]:
    """Extrai itens e quantidades da mensagem do cliente"""
    text = _norm(message)
    items = []
    
    # Padrões para detectar quantidades + produtos
    patterns = [
        r'(\d+(?:[.,]\d+)?)\s*(kg|quilo|quilos|gramas?|g)\s+(?:de\s+)?([a-záàãâçéêíóôõú\s]+)',
        r'(\d+(?:[.,]\d+)?)\s*([a-záàãâçéêíóôõú\s]+?)(?:\s+(?:kg|quilo|quilos|gramas?|g))?',
        r'(?:quero|preciso|vou levar|me vende)\s+(\d+(?:[.,]\d+)?)\s*(?:kg|quilo|quilos|gramas?|g)?\s*(?:de\s+)?([a-záàãâçéêíóôõú\s]+)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if len(match.groups()) == 3:  # quantidade, unidade, produto
                    quantidade_str, unidade, produto = match.groups()
                else:  # quantidade, produto
                    quantidade_str, produto = match.groups()
                    unidade = 'kg'  # default
                
                # Limpa quantidade
                quantidade = float(quantidade_str.replace(',', '.'))
                
                # Limpa produto
                produto = produto.strip()
                if len(produto) >= 3:  # produto mínimo 3 chars
                    items.append({
                        'produto': produto,
                        'quantidade': quantidade,
                        'unidade': unidade,
                        'preco_unitario': None,
                        'preco_total': None
                    })
            except (ValueError, AttributeError):
                continue
    
    return items

def _match_product_in_catalog(item_name: str, catalog_items: List[Dict[str, str]]) -> Dict[str, Any]:
    """Encontra produto no catálogo com matching inteligente"""
    item_norm = _norm(item_name)
    
    # Busca exata primeiro
    for catalog_item in catalog_items:
        desc = _norm(catalog_item.get('descricao', '') or catalog_item.get('produto', ''))
        if item_norm in desc or desc in item_norm:
            return {
                'found': True,
                'product': catalog_item,
                'confidence': 'alta',
                'match_type': 'exata'
            }
    
    # Busca por palavras-chave
    item_words = set(item_norm.split())
    best_match = None
    best_score = 0
    
    for catalog_item in catalog_items:
        desc = _norm(catalog_item.get('descricao', '') or catalog_item.get('produto', ''))
        desc_words = set(desc.split())
        
        # Calcula score de similaridade
        intersection = item_words.intersection(desc_words)
        score = len(intersection) / max(len(item_words), len(desc_words))
        
        if score > best_score and score > 0.3:  # threshold mínimo
            best_score = score
            best_match = catalog_item
    
    if best_match:
        confidence = 'alta' if best_score > 0.7 else 'média' if best_score > 0.5 else 'baixa'
        return {
            'found': True,
            'product': best_match,
            'confidence': confidence,
            'match_type': 'similar',
            'score': best_score
        }
    
    return {
        'found': False,
        'suggestions': _get_similar_products(item_name, catalog_items)
    }

def _get_similar_products(item_name: str, catalog_items: List[Dict[str, str]]) -> List[str]:
    """Retorna produtos similares baseado na busca"""
    item_norm = _norm(item_name)
    suggestions = []
    
    # Categorias para sugestão
    categorias = {
        'carne': ['picanha', 'alcatra', 'contrafilé', 'maminha', 'patinho'],
        'frango': ['coxa', 'sobrecoxa', 'peito', 'asa'],
        'porco': ['pernil', 'costela', 'lombo', 'calabresa', 'linguiça'],
        'frios': ['presunto', 'mortadela', 'queijo', 'salame']
    }
    
    for categoria, produtos in categorias.items():
        if any(word in item_norm for word in [categoria] + produtos):
            # Busca produtos desta categoria no catálogo
            for catalog_item in catalog_items:
                desc = _norm(catalog_item.get('descricao', ''))
                if any(p in desc for p in produtos):
                    produto_nome = catalog_item.get('descricao', catalog_item.get('produto', ''))
                    if produto_nome not in suggestions:
                        suggestions.append(produto_nome)
                        if len(suggestions) >= 3:
                            break
            break
    
    return suggestions[:3]

def _calculate_order_total(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula total do pedido incluindo taxa de entrega"""
    service_utils = get_service_utils()
    
    subtotal = 0
    items_validos = 0
    
    for item in items:
        if item.get('preco_total'):
            subtotal += float(item['preco_total'])
            items_validos += 1
    
    # Taxa de entrega (simulada - seria calculada baseada no CEP real)
    taxa_entrega = 0  # Default grátis até 3km
    
    total = subtotal + taxa_entrega
    
    return {
        'subtotal': subtotal,
        'taxa_entrega': taxa_entrega,
        'total': total,
        'items_validos': items_validos,
        'formatado': {
            'subtotal': service_utils.formatar_valor_monetario(subtotal),
            'taxa_entrega': service_utils.formatar_valor_monetario(taxa_entrega) if taxa_entrega > 0 else "Grátis",
            'total': service_utils.formatar_valor_monetario(total)
        }
    }

def _format_order_summary(items: List[Dict[str, Any]], totals: Dict[str, Any]) -> str:
    """Formata resumo do pedido de forma clara"""
    if not items:
        return "📋 Seu carrinho está vazio."
    
    linhas = ["📋 **Resumo do seu pedido:**\n"]
    
    # Itens do pedido
    for i, item in enumerate(items, 1):
        if item.get('produto_encontrado'):
            produto = item['produto_encontrado']['product']
            desc = produto.get('descricao', produto.get('produto', 'Produto'))
            preco_unit = produto.get('preco', 'N/A')
            quantidade = item['quantidade']
            unidade = item.get('unidade', 'kg')
            
            if item.get('preco_total'):
                preco_total = f"R$ {item['preco_total']:.2f}"
            else:
                preco_total = "A calcular"
            
            linhas.append(f"{i}. {desc}")
            linhas.append(f"   📏 {quantidade}{unidade} × R$ {preco_unit} = {preco_total}")
        else:
            linhas.append(f"{i}. {item['produto']} ({item['quantidade']}{item.get('unidade', 'kg')})")
            linhas.append(f"   ❓ Produto não encontrado - precisa validar")
    
    linhas.append("")
    
    # Totais
    if totals['items_validos'] > 0:
        linhas.append(f"💰 **Subtotal:** {totals['formatado']['subtotal']}")
        linhas.append(f"🚚 **Entrega:** {totals['formatado']['taxa_entrega']}")
        linhas.append(f"🎯 **Total:** {totals['formatado']['total']}")
    else:
        linhas.append("💰 **Total:** A calcular após validar produtos")
    
    return "\n".join(linhas)

def respond(message: str, context: dict | None = None):
    """
    Roberto - Especialista em pedidos da 3A Frios
    Gestão inteligente de carrinho e processo de compra com insights do Bruno
    """
    text = (message or '').lower()
    acao_especial = None
    
    logger.info(f"[Pedidos] Roberto processando: '{message[:50]}...'")
    logger.info(f"[Pedidos] Contexto recebido - keys: {list((context or {}).keys())}")
    
    # Recuperar contexto
    conversation_history = context.get('conversation_history', []) if context else []
    catalog_items = context.get('catalog_items', []) if context else []
    
    # === INSIGHTS DO BRUNO ANALISTA INVISÍVEL ===
    bruno_insights = context.get('bruno_insights') if context else None
    roberto_sales_approach = ""
    
    if bruno_insights:
        lead_score = bruno_insights.get('lead_score', 0)
        status = bruno_insights.get('qualificacao_status', 'unknown')
        segmento = bruno_insights.get('segmento', 'unknown')
        urgencia = bruno_insights.get('urgencia', 'baixa')
        pessoas = bruno_insights.get('pessoas')
        
        logger.info(f"[Roberto] Bruno insights: score={lead_score}, status={status}, urgencia={urgencia}")
        
        # Abordagem de vendas baseada nos insights
        if status == 'hot':
            roberto_sales_approach = "🔥 LEAD QUENTE - Facilite o fechamento, ofereça condições especiais!"
        elif status == 'warm':
            roberto_sales_approach = "🌡️ LEAD MORNO - Construa valor, calcule tudo detalhadamente!"
        elif status == 'cold':
            roberto_sales_approach = "❄️ LEAD FRIO - Seja educativo, mostre processo simples!"
            
        if urgencia == 'alta':
            roberto_sales_approach += " | ⚡ URGENTE - Priorize rapidez no atendimento!"
            
        if pessoas and pessoas > 15:
            roberto_sales_approach += f" | 👥 EVENTO GRANDE ({pessoas} pessoas) - Sugira desconto por volume!"
            
        if segmento == 'pessoa_juridica':
            roberto_sales_approach += " | 🏢 B2B - Ofereça condições empresariais e faturamento!"
    
    logger.info(f"[Pedidos] Roberto com {len(catalog_items)} produtos no catálogo")
    
    # === DETECÇÃO DE TIPOS DE AÇÃO ===
    is_greeting = any(k in text for k in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite'])
    is_adding_items = any(k in text for k in ['quero', 'vou levar', 'preciso', 'me vende', 'adicionar'])
    is_confirming = any(k in text for k in ['confirmar', 'finalizar', 'fechar pedido', 'tá certo', 'ok'])
    is_asking_info = any(k in text for k in ['total', 'quanto fica', 'valor', 'entrega', 'pagamento'])
    
    # Detecta se tem itens na mensagem
    items_detectados = _extract_items_from_message(message)
    
    # === LÓGICA PRINCIPAL DO ROBERTO ===
    
    # Saudação inicial
    if is_greeting and not items_detectados and not is_adding_items:
        conv_type = "primeira_interacao" if not conversation_history else "conversa_ativa"
        if conv_type == "primeira_interacao":
            resposta = f"""Oi! Eu sou o Roberto, especialista em pedidos da 3A Frios! 📋🥩

Estou aqui para te ajudar a montar seu pedido com muito cuidado e atenção. Posso:

🛒 Organizar seus itens no carrinho
💰 Calcular valores e total do pedido  
📍 Verificar taxa de entrega por CEP
💳 Explicar formas de pagamento

Me conte: o que você gostaria de pedir hoje?"""
        else:
            resposta = f"Oi! Roberto aqui novamente! 😊 Vamos continuar com seu pedido?"
        
        return {
            'resposta': resposta,
            'acao_especial': acao_especial,
        }
    
    # Cliente está adicionando itens
    if items_detectados or is_adding_items:
        acao_especial = '[ACAO:CRIAR_OU_ATUALIZAR_PEDIDO]'
        
        if items_detectados:
            logger.info(f"[Pedidos] Roberto identificou {len(items_detectados)} itens")
            
            # Processa itens com catálogo
            carrinho = []
            itens_validados = 0
            itens_nao_encontrados = []
            
            for item in items_detectados:
                if catalog_items:
                    resultado = _match_product_in_catalog(item['produto'], catalog_items)
                    item['produto_encontrado'] = resultado
                    
                    if resultado['found']:
                        produto = resultado['product']
                        preco_unit = float(produto.get('preco', '0').replace(',', '.'))
                        preco_total = preco_unit * item['quantidade']
                        
                        item['preco_unitario'] = preco_unit
                        item['preco_total'] = preco_total
                        itens_validados += 1
                    else:
                        itens_nao_encontrados.append(item)
                
                carrinho.append(item)
            
            # Calcula totais
            totals = _calculate_order_total(carrinho)
            
            # Constrói resposta
            if itens_validados > 0:
                resumo = _format_order_summary(carrinho, totals)
                
                if itens_nao_encontrados:
                    resposta = f"""Oi! Roberto da 3A Frios aqui! 😊

{resumo}

⚠️ **Atenção:** Alguns itens do seu carrinho precisam ser validados:
"""
                    for item in itens_nao_encontrados:
                        sugestoes = item['produto_encontrado'].get('suggestions', [])
                        if sugestoes:
                            resposta += f"\n❓ '{item['produto']}' - Você quis dizer: {', '.join(sugestoes[:2])}?"
                        else:
                            resposta += f"\n❓ '{item['produto']}' - Não encontrei este produto"
                    
                    resposta += f"\n\n💬 Me confirma os produtos corretos que eu atualizo seu carrinho!"
                else:
                    resposta = f"""Perfeito! Roberto aqui organizou seu carrinho! 🎯

{resumo}

✅ **Próximos passos:**
• Me informe seu CEP para calcular a entrega
• Escolha a forma de pagamento  
• Confirme o pedido

💬 Quer adicionar mais alguma coisa no carrinho ou posso prosseguir?"""
            
            else:
                # Nenhum item foi validado
                resposta = f"""Oi! Roberto da 3A Frios aqui! 😊

Entendi que você quer fazer um pedido, mas preciso validar os produtos:

"""
                for item in items_detectados:
                    sugestoes = item.get('produto_encontrado', {}).get('suggestions', [])
                    if sugestoes:
                        resposta += f"❓ '{item['produto']}' - Você quis dizer: {', '.join(sugestoes[:2])}?\n"
                    else:
                        resposta += f"❓ '{item['produto']}' - Não encontrei este produto\n"
                
                resposta += f"\n💡 **Dica:** Posso te ajudar! Me fale que tipo de carne ou produto você está procurando que eu encontro as opções disponíveis!"
        
        else:
            # Cliente quer adicionar mas não especificou itens
            resposta = f"""Oi! Roberto da 3A Frios! 😊🛒

Perfeito, vamos montar seu pedido! Me conte:

📝 **Que produtos você quer?**
📏 **Qual quantidade de cada um?**

Exemplo: "Quero 1kg de picanha e 500g de linguiça"

Estou aqui para organizar tudo certinho para você! 💪"""
    
    # Cliente perguntando sobre informações do pedido
    elif is_asking_info:
        resposta = f"""Oi! Roberto aqui! 📊

**Informações importantes sobre seu pedido:**

💳 **Formas de pagamento:**
• Dinheiro na entrega
• Cartão na entrega  
• PIX
• Transferência bancária

🚚 **Taxa de entrega:**
• Até 3km: Grátis
• 3km a 5km: R$ 3,00
• Acima de 5km: R$ 5,00

💰 **Total:** Será calculado com base nos itens do seu carrinho + entrega
⏰ **Prazo:** 24-48h na região
📞 **Pedidos:** {DELIVERY_INFO['horario_pedidos']}

💬 Já tem produtos em mente ou quer que eu te ajude a escolher?"""
    
    # Fallback inteligente do Roberto
    else:
        # Usa OpenAI para casos complexos
        if catalog_items:
            catalog_preview = "\n".join([
                f"• {item.get('descricao', item.get('produto', ''))} - R$ {item.get('preco', 'N/A')}"
                for item in catalog_items[:8]
            ])
            
            prompt = f"""Você é o Roberto, especialista em pedidos da 3A Frios.

PERSONALIDADE:
- Nome: Roberto, especialista em pedidos
- Tom: eficiente, atencioso e organizador  
- Sempre se apresente como Roberto da 3A Frios
- Use emojis relacionados a pedidos (📋🛒💰🚚)
- Seja preciso com valores e informações
- Guie o cliente pelo processo passo a passo

CATÁLOGO DISPONÍVEL:
{catalog_preview}

FORMAS DE PAGAMENTO: Dinheiro, Cartão, PIX, Transferência
ENTREGA: Grátis até 3km, R$ 3,00 (3-5km), R$ 5,00 (+5km)
PRAZO: 24-48h na região

INSTRUÇÃO: Ajude o cliente com seu pedido de forma organizada e eficiente."""

            try:
                ai_response = generate_response(prompt, message or '')
                if ai_response and len(ai_response.strip()) > 10:
                    resposta = ai_response.strip()
                    
                    # Garante que Roberto se apresentou
                    if 'Roberto' not in resposta:
                        resposta = f"Oi! Roberto da 3A Frios aqui! 😊📋 {resposta}"
                else:
                    raise Exception("Resposta AI inadequada")
                    
            except Exception as e:
                logger.error(f"[Pedidos] Roberto fallback: {e}")
                resposta = f"Oi! Roberto da 3A Frios! 😊📋 Estou aqui para te ajudar com seu pedido. Me conta o que você precisa que eu organizo tudo certinho!"
        
        else:
            resposta = f"Oi! Roberto da 3A Frios! 😊📋 Especialista em pedidos aqui! Me conta o que você quer pedir que eu organizo tudo para você!"
    
    logger.info(f"[Pedidos] Roberto finalizou: {len(resposta)} chars | Ação: {acao_especial}")
    
    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }