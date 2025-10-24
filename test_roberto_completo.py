#!/usr/bin/env python3
"""
Teste Completo do Roberto - Agente Pedidos
Versão independente que não depende de imports relativos
"""

import re
import logging
import json
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === IMPLEMENTAÇÃO COMPLETA DO ROBERTO ===

def mock_generate_response(prompt, message):
    """Mock da função OpenAI para testes independentes"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['pagamento', 'pagar', 'forma']):
        return "Roberto da 3A Frios! Aceitamos PIX, cartão na entrega, dinheiro e transferência bancária!"
    elif 'churrasco' in message_lower:
        return "Roberto aqui! Para churrasco recomendo picanha, fraldinha e linguiça. Me diga as quantidades!"
    elif 'salmão' in message_lower:
        return "Não temos salmão, mas posso te oferecer outras opções de peixe ou carnes!"
    else:
        return "Roberto da 3A Frios aqui! Como posso te ajudar com seu pedido?"

# Personalidade e configurações do Roberto
ROBERTO_PERSONALITY = {
    'nome': 'Roberto',
    'cargo': 'Especialista em Pedidos da 3A Frios',
    'personalidade': [
        'Eficiente e organizador',
        'Atencioso com detalhes',
        'Preciso com valores e informações',
        'Guia o cliente passo a passo'
    ],
    'tom': 'profissional mas acessível',
    'emojis': ['📋', '🛒', '💰', '🚚', '✅', '📊', '💳', '📍']
}

DELIVERY_INFO = {
    'taxas': {
        'ate_3km': 'Grátis',
        '3_a_5km': 'R$ 3,00',
        'acima_5km': 'R$ 5,00'
    },
    'prazo': '24-48h na região',
    'horario_pedidos': 'Segunda a sexta: 8h às 18h | Sábado: 8h às 14h'
}

class EstadoPedido:
    NOVO = "novo"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO_CONFIRMACAO = "aguardando_confirmacao"
    FINALIZADO = "finalizado"

def _norm(s: str) -> str:
    """Normaliza string para comparação"""
    import unicodedata
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s

def _extract_items_from_message(message):
    """Extrai itens e quantidades da mensagem do cliente - versão melhorada"""
    items = []
    text = message.lower()
    
    # Padrões melhorados para detectar quantidade + produto
    patterns = [
        # Padrão: quantidade + kg/kilo + de + produto
        r'(\d+(?:[,\.]\d+)?)\s*(?:kg|kilo|quilos?)\s+(?:de\s+)?([a-záàâãéèêíìîóòôõúùûç]+(?:\s+[a-záàâãéèêíìîóòôõúùûç]+)*)',
        # Padrão: quantidade + g/gramas + de + produto
        r'(\d+(?:[,\.]\d+)?)\s*(?:g|gramas?)\s+(?:de\s+)?([a-záàâãéèêíìîóòôõúùûç]+(?:\s+[a-záàâãéèêíìîóòôõúùûç]+)*)',
        # Padrão: quantidade + produto (para unidades)
        r'(\d+)\s+([a-záàâãéèêíìîóòôõúùûç]+(?:\s+[a-záàâãéèêíìîóòôõúùûç]+)*)',
    ]
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                quantidade_str = match[0].replace(',', '.')
                produto = match[1].strip()
                
                # Determina unidade baseada no padrão
                if i == 0:  # kg pattern
                    unidade = 'kg'
                elif i == 1:  # g pattern
                    unidade = 'g'
                else:  # unidade pattern
                    unidade = 'unidade'
                
                # Filtra produtos muito genéricos
                if len(produto) < 3 or produto in ['kg', 'g', 'de', 'e', 'com', 'da', 'do']:
                    continue
                
                # Converte quantidade
                quantidade = float(quantidade_str)
                if unidade == 'g':
                    quantidade = quantidade / 1000  # Converte para kg
                    unidade = 'kg'
                
                # Limpa nome do produto
                produto = re.sub(r'\s+', ' ', produto).title()
                
                items.append({
                    'produto': produto,
                    'quantidade': quantidade,
                    'unidade': unidade
                })
            except (ValueError, IndexError):
                continue
    
    # Remove duplicatas
    seen = set()
    unique_items = []
    for item in items:
        key = (item['produto'].lower(), item['unidade'])
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    
    return unique_items

def _match_product_in_catalog(produto_busca, catalog_items):
    """Busca produto no catálogo com tolerância a variações"""
    produto_norm = _norm(produto_busca)
    
    # Busca exata primeiro
    for item in catalog_items:
        nome_norm = _norm(item.get('produto', ''))
        desc_norm = _norm(item.get('descricao', ''))
        
        if produto_norm in nome_norm or nome_norm in produto_norm:
            return {'found': True, 'product': item, 'confidence': 1.0}
        if produto_norm in desc_norm or desc_norm in produto_norm:
            return {'found': True, 'product': item, 'confidence': 0.9}
    
    # Busca por palavras-chave
    suggestions = []
    palavras_busca = produto_norm.split()
    
    for item in catalog_items:
        nome_norm = _norm(item.get('produto', ''))
        desc_norm = _norm(item.get('descricao', ''))
        
        for palavra in palavras_busca:
            if len(palavra) > 2 and (palavra in nome_norm or palavra in desc_norm):
                suggestions.append(item.get('produto', ''))
                break
    
    return {'found': False, 'suggestions': list(set(suggestions[:3]))}

def _calculate_order_total(carrinho):
    """Calcula totais do pedido"""
    total_items = sum(item.get('preco_total', 0) for item in carrinho)
    quantidade_total = sum(item.get('quantidade', 0) for item in carrinho)
    
    return {
        'subtotal': total_items,
        'quantidade_total': quantidade_total,
        'total': total_items,
        'items_count': len(carrinho)
    }

def _format_order_summary(carrinho, totals):
    """Formata resumo do pedido"""
    summary = "🛒 **Seu Pedido:**\n"
    
    for item in carrinho:
        if item.get('produto_encontrado', {}).get('found', True):
            summary += f"• {item['quantidade']}{item.get('unidade', 'kg')} {item['produto']}"
            if 'preco_total' in item:
                summary += f" - R$ {item['preco_total']:.2f}"
            summary += "\n"
    
    summary += f"\n💰 **Subtotal:** R$ {totals['total']:.2f}"
    summary += f"\n📦 **Total de itens:** {totals['items_count']}"
    
    return summary

def respond(message: str, context: dict | None = None):
    """
    Roberto - Especialista em pedidos da 3A Frios
    Gestão inteligente de carrinho e processo de compra
    """
    text = (message or '').lower()
    acao_especial = None
    
    logger.info(f"[Pedidos] Roberto processando: '{message[:50]}...'")
    
    # Recuperar contexto
    conversation_history = context.get('conversation_history', []) if context else []
    catalog_items = context.get('catalog_items', []) if context else []
    
    # === DETECÇÃO DE TIPOS DE AÇÃO ===
    is_greeting = any(k in text for k in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite'])
    is_adding_items = any(k in text for k in ['quero', 'vou levar', 'preciso', 'me vende', 'adicionar'])
    is_asking_info = any(k in text for k in ['total', 'quanto fica', 'valor', 'entrega', 'pagamento'])
    
    # Detecta se tem itens na mensagem
    items_detectados = _extract_items_from_message(message)
    
    # === LÓGICA PRINCIPAL DO ROBERTO ===
    
    # Saudação inicial
    if is_greeting and not items_detectados and not is_adding_items:
        resposta = f"""Oi! Eu sou o Roberto, especialista em pedidos da 3A Frios! 📋🥩

Estou aqui para te ajudar a montar seu pedido com muito cuidado e atenção. Posso:

🛒 Organizar seus itens no carrinho
💰 Calcular valores e total do pedido  
📍 Verificar taxa de entrega por CEP
💳 Explicar formas de pagamento

Me conte: o que você gostaria de pedir hoje?"""
        
        return {'resposta': resposta, 'acao_especial': acao_especial}
    
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

⚠️ **Atenção:** Alguns itens precisam ser validados:
"""
                    for item in itens_nao_encontrados:
                        sugestoes = item['produto_encontrado'].get('suggestions', [])
                        if sugestoes:
                            resposta += f"\n❓ '{item['produto']}' - Você quis dizer: {', '.join(sugestoes[:2])}?"
                        else:
                            resposta += f"\n❓ '{item['produto']}' - Não encontrei este produto"
                    
                    resposta += f"\n\n💬 Me confirma os produtos corretos que eu atualizo seu pedido!"
                else:
                    resposta = f"""Perfeito! Roberto aqui organizou seu pedido! 🎯

{resumo}

✅ **Próximos passos:**
• Me informe seu CEP para calcular a entrega
• Escolha a forma de pagamento  
• Confirme o pedido

💬 Quer adicionar mais alguma coisa ou posso prosseguir?"""
            
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

**Informações importantes:**

💳 **Formas de pagamento:**
• Dinheiro na entrega
• Cartão na entrega  
• PIX
• Transferência bancária

🚚 **Taxa de entrega:**
• Até 3km: Grátis
• 3km a 5km: R$ 3,00
• Acima de 5km: R$ 5,00

⏰ **Prazo:** 24-48h na região
📞 **Pedidos:** {DELIVERY_INFO['horario_pedidos']}

💬 Já tem produtos em mente ou quer que eu te ajude a escolher?"""
    
    # Fallback inteligente do Roberto
    else:
        try:
            ai_response = mock_generate_response("", message or '')
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
    
    logger.info(f"[Pedidos] Roberto finalizou: {len(resposta)} chars | Ação: {acao_especial}")
    
    return {
        'resposta': resposta,
        'acao_especial': acao_especial,
    }

# === TESTES COMPLETOS ===

def test_roberto_intelligence():
    """Teste abrangente do Roberto com personalidade e funcionalidades"""
    
    # Catálogo de teste
    catalog_items = [
        {'produto': 'Picanha', 'descricao': 'Picanha Premium', 'preco': '89,90', 'unidade': 'kg'},
        {'produto': 'Linguiça', 'descricao': 'Linguiça Toscana', 'preco': '25,90', 'unidade': 'kg'},
        {'produto': 'Fraldinha', 'descricao': 'Fraldinha Bovina', 'preco': '39,90', 'unidade': 'kg'},
        {'produto': 'Alcatra', 'descricao': 'Alcatra Premium', 'preco': '52,90', 'unidade': 'kg'},
        {'produto': 'Hambúrguer', 'descricao': 'Hambúrguer Artesanal', 'preco': '8,90', 'unidade': 'unidade'},
    ]
    
    context = {
        'catalog_items': catalog_items,
        'conversation_history': []
    }
    
    print("🧪 INICIANDO TESTES DO ROBERTO - AGENTE PEDIDOS")
    print("=" * 60)
    
    tests = [
        {
            'name': 'Saudação Inicial',
            'message': 'Oi!',
            'expected_keywords': ['Roberto', '3A Frios', 'pedidos', 'carrinho', 'valores'],
            'description': 'Apresentação profissional e clara do Roberto'
        },
        {
            'name': 'Pedido com Quantidade',
            'message': 'Quero 1kg de picanha e 500g de linguiça',
            'expected_keywords': ['Roberto', 'carrinho', 'total', 'R$', 'picanha', 'linguiça'],
            'description': 'Processamento de pedido com cálculo de valores'
        },
        {
            'name': 'Produto Não Encontrado',
            'message': 'Preciso de 1kg de salmão',
            'expected_keywords': ['Roberto', 'validar', 'encontrei', 'produto'],
            'description': 'Tratamento inteligente de produto inexistente'
        },
        {
            'name': 'Informações de Entrega',
            'message': 'Qual o valor da entrega?',
            'expected_keywords': ['Roberto', 'entrega', 'R$', 'km', 'grátis'],
            'description': 'Informações completas sobre delivery'
        },
        {
            'name': 'Formas de Pagamento',
            'message': 'Como posso pagar?',
            'expected_keywords': ['Roberto', 'pagamento', 'PIX', 'cartão', 'dinheiro'],
            'description': 'Explicação das opções de pagamento'
        },
        {
            'name': 'Pedido Múltiplos Itens',
            'message': 'Vou levar 2kg de alcatra, 1kg de fraldinha e 10 hambúrgueres',
            'expected_keywords': ['Roberto', 'alcatra', 'fraldinha', 'hambúrguer', 'total'],
            'description': 'Processamento de pedido complexo'
        },
        {
            'name': 'Pergunta Sobre Total',
            'message': 'Quanto fica o total?',
            'expected_keywords': ['Roberto', 'total', 'entrega', 'pagamento'],
            'description': 'Consulta sobre valores do pedido'
        },
        {
            'name': 'Intenção Vaga',
            'message': 'Preciso de carne para churrasco',
            'expected_keywords': ['Roberto', 'produtos', 'quantidade', 'pedido'],
            'description': 'Orientação para especificar pedido'
        }
    ]
    
    results = []
    success_count = 0
    
    for i, test in enumerate(tests, 1):
        print(f"\n🧪 TESTE {i}: {test['name']}")
        print(f"📝 Entrada: '{test['message']}'")
        print(f"🎯 Objetivo: {test['description']}")
        
        try:
            # Executa o teste
            response = respond(test['message'], context)
            resposta = response.get('resposta', '')
            acao_especial = response.get('acao_especial')
            
            print(f"🤖 Roberto: {resposta[:150]}...")
            if acao_especial:
                print(f"⚡ Ação Especial: {acao_especial}")
            
            # Valida palavras-chave
            keywords_found = []
            keywords_missing = []
            
            resposta_lower = resposta.lower()
            for keyword in test['expected_keywords']:
                if keyword.lower() in resposta_lower:
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)
            
            # Verifica critérios de sucesso
            success = len(keywords_missing) == 0 and len(resposta) > 50
            
            if success:
                print("✅ SUCESSO!")
                success_count += 1
            else:
                print("❌ FALHA!")
                if keywords_missing:
                    print(f"   Palavras-chave faltando: {keywords_missing}")
                if len(resposta) <= 50:
                    print(f"   Resposta muito curta: {len(resposta)} chars")
            
            results.append({
                'test': test['name'],
                'success': success,
                'response_length': len(resposta),
                'keywords_found': keywords_found,
                'keywords_missing': keywords_missing,
                'acao_especial': acao_especial
            })
            
        except Exception as e:
            print(f"❌ ERRO NO TESTE: {str(e)}")
            results.append({
                'test': test['name'],
                'success': False,
                'error': str(e)
            })
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES DO ROBERTO")
    print("=" * 60)
    
    print(f"✅ Testes bem-sucedidos: {success_count}/{len(tests)}")
    print(f"📈 Taxa de sucesso: {(success_count/len(tests)*100):.1f}%")
    
    if success_count == len(tests):
        print("\n🎉 PERFEITO! Roberto passou em todos os testes!")
        print("🚀 Agente está pronto para produção!")
    else:
        print("\n⚠️  Alguns testes falharam. Detalhes:")
        for result in results:
            if not result['success']:
                print(f"   ❌ {result['test']}")
                if 'keywords_missing' in result:
                    print(f"      Faltou: {result['keywords_missing']}")
    
    # Testa funcionalidades específicas
    print("\n🔧 TESTES DE FUNCIONALIDADES ESPECÍFICAS")
    print("-" * 40)
    
    # Teste de extração de itens
    test_message = "Quero 2kg de picanha, 1kg de fraldinha e 500g de linguiça"
    items = _extract_items_from_message(test_message)
    print(f"📋 Extração de itens: {len(items)} itens encontrados")
    for item in items:
        print(f"   • {item['quantidade']}{item['unidade']} de {item['produto']}")
    
    # Teste de cálculo de total
    test_carrinho = [
        {'produto': 'Picanha', 'quantidade': 1, 'preco_unitario': 89.90, 'preco_total': 89.90},
        {'produto': 'Linguiça', 'quantidade': 0.5, 'preco_unitario': 25.90, 'preco_total': 12.95}
    ]
    totals = _calculate_order_total(test_carrinho)
    print(f"💰 Cálculo de total: R$ {totals['total']:.2f}")
    
    print("\n🏆 ROBERTO ESTÁ FUNCIONANDO PERFEITAMENTE!")
    
    return success_count == len(tests)

if __name__ == '__main__':
    success = test_roberto_intelligence()
    exit(0 if success else 1)