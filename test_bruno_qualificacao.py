#!/usr/bin/env python3
"""
Teste do Bruno - Agente Qualificação
Valida nova inteligência com personalidade e capacidades de descoberta
"""

import sys
import os
import importlib.util
import json

# Adiciona o diretório raiz e server ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'server'))

# Carrega o módulo qualificacao diretamente
qualificacao_path = os.path.join(current_dir, 'server', 'agents', 'qualificacao.py')
spec = importlib.util.spec_from_file_location("qualificacao", qualificacao_path)
qualificacao_module = importlib.util.module_from_spec(spec)

# Mock da função generate_response para evitar dependência da OpenAI
def mock_generate_response(prompt, message):
    """Mock da função OpenAI para testes"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['quanto', 'preço', 'valor']):
        return "Bruno da 3A Frios! Para dar um orçamento preciso, preciso saber: quantas pessoas, que tipo de evento e qual seu prazo?"
    elif 'empresa' in message_lower or 'restaurante' in message_lower:
        return "Bruno aqui! Vejo que é para uso empresarial. Me conta: qual o volume mensal que vocês trabalham e se é demanda regular?"
    elif 'festa' in message_lower or 'aniversário' in message_lower:
        return "Bruno da 3A Frios! Que legal, uma festa! Para quantas pessoas será? Já tem data definida?"
    else:
        return "Bruno da 3A Frios aqui! Para te qualificar melhor, me conta mais sobre o que você está planejando!"

# Injeta o mock no módulo antes de carregar
sys.modules['openai_client'] = type('MockModule', (), {'generate_response': mock_generate_response})()

# Carrega o módulo
spec.loader.exec_module(qualificacao_module)

# Importa as funções necessárias
respond = qualificacao_module.respond
_detect_client_segment = qualificacao_module._detect_client_segment
_detect_need_type = qualificacao_module._detect_need_type
_extract_context_clues = qualificacao_module._extract_context_clues

def test_bruno_intelligence():
    """Teste abrangente do Bruno com personalidade e funcionalidades"""
    
    # Catálogo de teste
    catalog_items = [
        {'produto': 'Picanha', 'descricao': 'Picanha Premium', 'preco': '89,90'},
        {'produto': 'Linguiça', 'descricao': 'Linguiça Toscana', 'preco': '25,90'},
        {'produto': 'Fraldinha', 'descricao': 'Fraldinha Bovina', 'preco': '39,90'},
        {'produto': 'Alcatra', 'descricao': 'Alcatra Premium', 'preco': '52,90'},
    ]
    
    context = {
        'catalog_items': catalog_items,
        'conversation_history': []
    }
    
    print("🧪 INICIANDO TESTES DO BRUNO - AGENTE QUALIFICAÇÃO")
    print("=" * 60)
    
    tests = [
        {
            'name': 'Saudação Inicial',
            'message': 'Oi!',
            'expected_keywords': ['Bruno', '3A Frios', 'qualificação', 'necessidades', 'planejando'],
            'description': 'Apresentação consultiva e descoberta'
        },
        {
            'name': 'Evento Familiar',
            'message': 'Estou organizando um churrasco para a família, somos 15 pessoas',
            'expected_keywords': ['Bruno', 'pessoas', 'perguntas', 'qualificar', 'ocasião'],
            'description': 'Qualificação de evento familiar com contexto'
        },
        {
            'name': 'Demanda Empresarial',
            'message': 'Preciso de carnes para nosso restaurante',
            'expected_keywords': ['Bruno', 'volume', 'regular', 'empresarial', 'investimento'],
            'description': 'Identificação e qualificação de cliente PJ'
        },
        {
            'name': 'Evento Especial',
            'message': 'Vou fazer uma festa de casamento',
            'expected_keywords': ['Bruno', 'convidados', 'data', 'especial', 'serviço'],
            'description': 'Qualificação de evento especial'
        },
        {
            'name': 'Urgência',
            'message': 'Preciso urgente para amanhã',
            'expected_keywords': ['Bruno', 'urgente', 'priorizar', 'quando', 'prazo'],
            'description': 'Detecção e tratamento de urgência'
        },
        {
            'name': 'Pergunta sobre Preço',
            'message': 'Quanto custa a picanha?',
            'expected_keywords': ['Bruno', 'orçamento', 'pessoas', 'evento', 'prazo'],
            'description': 'Qualificação antes de dar preços'
        },
        {
            'name': 'Primeira Vez',
            'message': 'É a primeira vez que vou comprar, não sei o que escolher',
            'expected_keywords': ['Bruno', 'descoberta', 'perguntas', 'ocasião', 'pessoas'],
            'description': 'Orientação para cliente descoberta'
        },
        {
            'name': 'Comparação',
            'message': 'Estou comparando preços com outros fornecedores',
            'expected_keywords': ['Bruno', 'outros lugares', 'comparação', 'qualificar', 'necessidades'],
            'description': 'Tratamento de cliente comparativo'
        }
    ]
    
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
            
            print(f"🤖 Bruno: {resposta[:150]}...")
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
            
        except Exception as e:
            print(f"❌ ERRO NO TESTE: {str(e)}")
            success_count -= 1  # Penaliza erro
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES DO BRUNO")
    print("=" * 60)
    
    print(f"✅ Testes bem-sucedidos: {success_count}/{len(tests)}")
    print(f"📈 Taxa de sucesso: {(success_count/len(tests)*100):.1f}%")
    
    if success_count == len(tests):
        print("\n🎉 PERFEITO! Bruno passou em todos os testes!")
        print("🚀 Agente está pronto para produção!")
    else:
        print(f"\n⚠️ {len(tests)-success_count} testes falharam")
    
    # Testa funcionalidades específicas
    print("\n🔧 TESTES DE FUNCIONALIDADES ESPECÍFICAS")
    print("-" * 40)
    
    # Teste de detecção de segmento
    test_messages = [
        "Organizando churrasco para a família",
        "Preciso para nosso restaurante",
        "Festa de casamento"
    ]
    
    for msg in test_messages:
        segment = _detect_client_segment(msg)
        print(f"📋 '{msg}' → Segmento: {segment}")
    
    # Teste de extração de contexto
    test_context = "Somos 20 pessoas, preciso para amanhã"
    clues = _extract_context_clues(test_context)
    print(f"🔍 Contexto extraído: {clues}")
    
    print("\n🏆 BRUNO TESTADO COM SUCESSO!")
    
    return success_count == len(tests)

if __name__ == '__main__':
    success = test_bruno_intelligence()
    exit(0 if success else 1)