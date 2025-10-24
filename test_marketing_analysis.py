#!/usr/bin/env python3
"""
Análise do Agente de Marketing
Avalia o estado atual e identifica oportunidades de melhoria
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from agents import marketing

def test_marketing_current_state():
    """Testa o estado atual do agente de marketing"""
    
    print("📢 ANÁLISE DO AGENTE DE MARKETING")
    print("=" * 50)
    
    test_cases = [
        # Casos relacionados a marketing
        {
            'input': 'Quero saber sobre promoções',
            'expected_topic': 'Promoções/Campanhas',
            'should_trigger_action': True
        },
        {
            'input': 'Tem alguma campanha especial?',
            'expected_topic': 'Campanhas',
            'should_trigger_action': True
        },
        {
            'input': 'Vocês fazem desconto para grandes quantidades?',
            'expected_topic': 'Descontos',
            'should_trigger_action': True
        },
        {
            'input': 'Como faço para receber newsletter?',
            'expected_topic': 'Newsletter',
            'should_trigger_action': True
        },
        # Casos não relacionados
        {
            'input': 'Quero comprar carne',
            'expected_topic': 'Geral',
            'should_trigger_action': False
        },
        {
            'input': 'Qual o horário de funcionamento?',
            'expected_topic': 'Atendimento',
            'should_trigger_action': False
        }
    ]
    
    print("🧪 TESTANDO CASOS DE USO:\n")
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. Entrada: '{case['input']}'")
        
        # Testa resposta
        response = marketing.respond(case['input'])
        
        print(f"   Resposta: {response['resposta']}")
        print(f"   Ação: {response['acao_especial'] or 'Nenhuma'}")
        
        # Valida expectativas
        has_action = response['acao_especial'] is not None
        action_match = has_action == case['should_trigger_action']
        
        status = "✅" if action_match else "❌"
        print(f"   Status: {status}")
        print()
    
    print("\n🔍 ANÁLISE DO CÓDIGO ATUAL:")
    print("📋 Funcionalidades Identificadas:")
    print("   • Detecção básica de palavras-chave de marketing")
    print("   • Resposta genérica sobre campanhas")
    print("   • Ação especial: [ACAO:ENVIAR_CAMPANHA]")
    
    print("\n🚨 LIMITAÇÕES ENCONTRADAS:")
    print("   ❌ Sem personalidade específica")
    print("   ❌ Respostas muito genéricas")
    print("   ❌ Não utiliza insights do Bruno")
    print("   ❌ Não segmenta campanhas por perfil")
    print("   ❌ Não sugere promoções específicas")
    print("   ❌ Não considera histórico do cliente")
    print("   ❌ Não integra com dados de vendas")
    
    print("\n💡 OPORTUNIDADES DE MELHORIA:")
    print("   🎯 Personalidade de especialista em marketing")
    print("   🔥 Integração com insights do Bruno")
    print("   📊 Campanhas segmentadas (B2B, eventos, família)")
    print("   💰 Promoções baseadas no valor potencial")
    print("   📈 Análise de padrões de compra")
    print("   🎪 Campanhas sazonais e por ocasião")
    print("   📱 Multi-canal (WhatsApp, email, SMS)")
    
    print("\n🎨 PERFIL SUGERIDO - 'CAMILA MARKETING':")
    print("   👩‍💼 Especialista em marketing e relacionamento")
    print("   🎯 Estratégica e orientada a resultados")
    print("   💡 Criativa com campanhas personalizadas")
    print("   📊 Data-driven para decisões")
    print("   🤝 Focada em relacionamento duradouro")
    
    return True

def test_marketing_scenarios():
    """Testa cenários específicos que o marketing deveria cobrir"""
    
    print("\n🎬 CENÁRIOS PARA O NOVO MARKETING:")
    print("=" * 50)
    
    scenarios = [
        {
            'name': 'Cliente B2B interessado em fornecimento',
            'bruno_insights': {
                'segmento': 'pessoa_juridica',
                'lead_score': 7,
                'interesse_compra': 8,
                'qualificacao_status': 'hot'
            },
            'message': 'Vocês fazem desconto para restaurante?',
            'expected_behavior': 'Campanha B2B com condições especiais, parcerias, volumes'
        },
        {
            'name': 'Evento especial urgente',
            'bruno_insights': {
                'segmento': 'evento_especial',
                'lead_score': 9,
                'urgencia': 'alta',
                'pessoas': 50
            },
            'message': 'Preciso de carne para um churrasco amanhã',
            'expected_behavior': 'Pacote evento express, entrega urgente, menu completo'
        },
        {
            'name': 'Família novo cliente',
            'bruno_insights': {
                'segmento': 'pessoa_fisica',
                'lead_score': 3,
                'qualificacao_status': 'cold'
            },
            'message': 'Primeira vez comprando aqui',
            'expected_behavior': 'Campanha boas-vindas, desconto primeira compra, fidelização'
        },
        {
            'name': 'Cliente frequente há tempo sem comprar',
            'bruno_insights': {
                'segmento': 'pessoa_fisica',
                'lead_score': 4,
                'ultima_compra': '2024-08-15'
            },
            'message': 'Faz tempo que não compro carne boa',
            'expected_behavior': 'Campanha reativação, ofertas especiais, novidades'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}:")
        print(f"   Mensagem: '{scenario['message']}'")
        print(f"   Insights Bruno: {scenario['bruno_insights']}")
        print(f"   Comportamento esperado: {scenario['expected_behavior']}")
    
    print("\n🏆 META PARA O NOVO MARKETING:")
    print("   • Campanhas 100% personalizadas")
    print("   • Integração total com insights do Bruno")
    print("   • ROI mensurado e otimizado")
    print("   • Experiência premium para cada segmento")
    
    return True

if __name__ == '__main__':
    print("🚀 INICIANDO ANÁLISE COMPLETA DO MARKETING\n")
    
    success1 = test_marketing_current_state()
    success2 = test_marketing_scenarios()
    
    print("\n" + "=" * 50)
    print("📊 RESULTADO DA ANÁLISE:")
    
    if success1 and success2:
        print("✅ Análise completa realizada")
        print("🎯 Pronto para implementar Camila Marketing!")
        print("🚀 Próximo passo: Desenvolver agente inteligente")
    else:
        print("❌ Problemas encontrados na análise")
    
    exit(0 if (success1 and success2) else 1)