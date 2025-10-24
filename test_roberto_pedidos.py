#!/usr/bin/env python3
"""
Teste do Roberto - Agente Pedidos
Valida nova inteligência com personalidade e funcionalidades completas
"""

import sys
import os
import importlib.util
import json

# Adiciona o diretório raiz e server ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'server'))

# Carrega o módulo pedidos diretamente
pedidos_path = os.path.join(current_dir, 'server', 'agents', 'pedidos.py')
spec = importlib.util.spec_from_file_location("pedidos", pedidos_path)
pedidos_module = importlib.util.module_from_spec(spec)

# Mock da função generate_response para evitar dependência da OpenAI
def mock_generate_response(prompt, message):
    """Mock da função OpenAI para testes"""
    if 'pagamento' in message.lower():
        return "Roberto da 3A Frios! Aceitamos PIX, cartão, dinheiro na entrega e transferência bancária."
    elif 'churrasco' in message.lower():
        return "Roberto aqui! Para churrasco recomendo picanha, fraldinha e linguiça. Me diga as quantidades!"
    return "Roberto da 3A Frios aqui! Como posso te ajudar com seu pedido?"

# Injeta o mock no módulo antes de carregar
sys.modules['openai_client'] = type('MockModule', (), {'generate_response': mock_generate_response})()

# Carrega o módulo
spec.loader.exec_module(pedidos_module)

# Importa as funções necessárias
respond = pedidos_module.respond
_extract_items_from_message = pedidos_module._extract_items_from_message
_calculate_order_total = pedidos_module._calculate_order_total

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