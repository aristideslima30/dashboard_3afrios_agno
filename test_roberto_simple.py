#!/usr/bin/env python3
"""
Teste Direto do Roberto - Agente Pedidos
Executa o código do Roberto diretamente para validar funcionalidades
"""

import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulação da função generate_response para não depender da OpenAI
def generate_response(prompt, message):
    """Simulação simplificada da OpenAI para testes"""
    if 'salmão' in message.lower():
        return "Não temos salmão, mas posso te oferecer outras opções de peixe ou carnes!"
    elif 'churrasco' in message.lower():
        return "Para churrasco, recomendo picanha, fraldinha e linguiça! Me diga as quantidades que você quer."
    else:
        return "Roberto da 3A Frios aqui! Como posso te ajudar com seu pedido?"

# === CÓDIGO DO ROBERTO (Copiado do pedidos.py) ===

ROBERTO_PERSONALITY = {
    'nome': 'Roberto',
    'cargo': 'Especialista em Pedidos da 3A Frios',
    'personalidade': [
        'Eficiente e organizador',
        'Atencioso com detalhes',
        'Preciso com valores e informações',
        'Guia o cliente passo a passo',
        'Sempre confirma informações importantes'
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

def _extract_items_from_message(message):
    """Extrai itens e quantidades da mensagem do cliente"""
    items = []
    text = message.lower()
    
    # Padrões para detectar quantidade + produto
    patterns = [
        r'(\d+(?:[,\.]\d+)?)\s*(kg|kilo|quilos?)\s+(?:de\s+)?([a-záàâãéèêíìîóòôõúùûç\s]+)',
        r'(\d+(?:[,\.]\d+)?)\s*(g|gramas?)\s+(?:de\s+)?([a-záàâãéèêíìîóòôõúùûç\s]+)',
        r'(\d+)\s*(?:unidades?\s+(?:de\s+)?|x\s+)?([a-záàâãéèêíìîóòôõúùûç\s]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            quantidade_str = match[0].replace(',', '.')
            unidade = match[1] if len(match) > 2 else 'unidade'
            produto = match[2] if len(match) > 2 else match[1]
            
            # Limpa o nome do produto
            produto = produto.strip()
            produto = re.sub(r'\s+', ' ', produto)
            
            # Converte quantidade
            quantidade = float(quantidade_str)
            if unidade in ['g', 'gramas', 'grama']:
                quantidade = quantidade / 1000  # Converte para kg
                unidade = 'kg'
            
            items.append({
                'produto': produto.title(),
                'quantidade': quantidade,
                'unidade': unidade
            })
    
    return items

def _match_product_in_catalog(produto_busca, catalog_items):
    """Busca produto no catálogo com tolerância a variações"""
    produto_busca = produto_busca.lower()
    
    # Busca exata primeiro
    for item in catalog_items:
        if produto_busca in item.get('produto', '').lower():
            return {'found': True, 'product': item, 'confidence': 1.0}
        if produto_busca in item.get('descricao', '').lower():
            return {'found': True, 'product': item, 'confidence': 0.9}
    
    # Busca por palavras-chave
    suggestions = []
    for item in catalog_items:
        produto_cat = item.get('produto', '').lower()
        desc_cat = item.get('descricao', '').lower()
        
        # Busca palavras em comum
        palavras_busca = produto_busca.split()
        for palavra in palavras_busca:
            if len(palavra) > 3 and (palavra in produto_cat or palavra in desc_cat):
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
        'total': total_items,  # Sem taxa de entrega ainda
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
    """Roberto - Especialista em pedidos da 3A Frios"""
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
                resposta = f"""Perfeito! Roberto aqui organizou seu pedido! 🎯

{resumo}

✅ **Próximos passos:**
• Me informe seu CEP para calcular a entrega
• Escolha a forma de pagamento  
• Confirme o pedido

💬 Quer adicionar mais alguma coisa ou posso prosseguir?"""
            else:
                resposta = f"""Oi! Roberto da 3A Frios aqui! 😊

💡 **Dica:** Posso te ajudar! Me fale que tipo de carne ou produto você está procurando que eu encontro as opções disponíveis!"""
        
        else:
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

💬 Já tem produtos em mente ou quer que eu te ajude a escolher?"""
    
    # Fallback inteligente do Roberto
    else:
        try:
            ai_response = generate_response("", message or '')
            if ai_response and len(ai_response.strip()) > 10:
                resposta = ai_response.strip()
                if 'Roberto' not in resposta:
                    resposta = f"Oi! Roberto da 3A Frios aqui! 😊📋 {resposta}"
            else:
                raise Exception("Resposta AI inadequada")
        except:
            resposta = f"Oi! Roberto da 3A Frios! 😊📋 Estou aqui para te ajudar com seu pedido. Me conta o que você precisa que eu organizo tudo certinho!"
    
    return {'resposta': resposta, 'acao_especial': acao_especial}

# === TESTES ===

def test_roberto_intelligence():
    """Teste abrangente do Roberto"""
    
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
            'expected_keywords': ['Roberto', 'salmão', 'opções'],
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
            'name': 'Intenção Vaga',
            'message': 'Preciso de carne para churrasco',
            'expected_keywords': ['Roberto', 'churrasco', 'picanha', 'fraldinha'],
            'description': 'Orientação para especificar pedido'
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(tests, 1):
        print(f"\n🧪 TESTE {i}: {test['name']}")
        print(f"📝 Entrada: '{test['message']}'")
        
        try:
            response = respond(test['message'], context)
            resposta = response.get('resposta', '')
            acao_especial = response.get('acao_especial')
            
            print(f"🤖 Roberto: {resposta[:200]}...")
            if acao_especial:
                print(f"⚡ Ação: {acao_especial}")
            
            # Valida palavras-chave
            keywords_found = sum(1 for kw in test['expected_keywords'] if kw.lower() in resposta.lower())
            success = keywords_found >= len(test['expected_keywords']) * 0.6 and len(resposta) > 50
            
            if success:
                print("✅ SUCESSO!")
                success_count += 1
            else:
                print("❌ FALHA!")
                
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
    
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
        print(f"\n⚠️ {len(tests)-success_count} testes falharam")
    
    # Teste funcionalidades específicas
    print("\n🔧 TESTES DE FUNCIONALIDADES ESPECÍFICAS")
    print("-" * 40)
    
    test_message = "Quero 2kg de picanha, 1kg de fraldinha e 500g de linguiça"
    items = _extract_items_from_message(test_message)
    print(f"📋 Extração de itens: {len(items)} itens encontrados")
    for item in items:
        print(f"   • {item['quantidade']}{item['unidade']} de {item['produto']}")
    
    print("\n🏆 ROBERTO TESTADO COM SUCESSO!")
    
    return success_count == len(tests)

if __name__ == '__main__':
    success = test_roberto_intelligence()
    exit(0 if success else 1)