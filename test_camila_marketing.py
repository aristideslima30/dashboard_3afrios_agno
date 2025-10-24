#!/usr/bin/env python3
"""
Teste Camila Marketing - Nova Especialista em Campanhas
Valida personalidade, segmentação e integração com Bruno
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from agents import marketing

def test_camila_personality():
    """Testa a personalidade da Camila Marketing"""
    
    print("👩‍💼 TESTANDO PERSONALIDADE CAMILA MARKETING")
    print("=" * 50)
    
    # Teste básico de apresentação
    response = marketing.respond("Oi, você tem promoções?")
    
    print("🎯 RESPOSTA DA CAMILA:")
    print(f"   {response['resposta'][:100]}...")
    print(f"   Ação: {response['acao_especial']}")
    
    # Verifica elementos da personalidade
    resposta_text = response['resposta']
    checks = {
        'Nome Camila': 'Camila' in resposta_text,
        'Tom profissional': any(word in resposta_text.lower() for word in ['especialista', 'marketing', '3a frios']),
        'Emoji/Visual': any(char in resposta_text for char in ['🎯', '💼', '✨', '🌟']),
        'Ação específica': response['acao_especial'] is not None
    }
    
    print("\n✅ ELEMENTOS DA PERSONALIDADE:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    return all(checks.values())

def test_segmentation_b2b():
    """Testa segmentação para clientes B2B"""
    
    print("\n🏢 TESTANDO SEGMENTAÇÃO B2B")
    print("=" * 50)
    
    bruno_insights = {
        'segmento': 'pessoa_juridica',
        'lead_score': 7,
        'qualificacao_status': 'hot',
        'interesse_compra': 8
    }
    
    context = {
        'bruno_insights': bruno_insights,
        'cliente': {'telefone': '+5511999998888'}
    }
    
    message = "Vocês fazem desconto para restaurante?"
    response = marketing.respond(message, context)
    
    print("📊 ENTRADA:")
    print(f"   Segmento Bruno: {bruno_insights['segmento']}")
    print(f"   Score: {bruno_insights['lead_score']}")
    print(f"   Mensagem: '{message}'")
    
    print("\n🎯 RESPOSTA CAMILA:")
    print(f"   {response['resposta'][:150]}...")
    print(f"   Ação: {response['acao_especial']}")
    
    # Verifica estratégia B2B
    strategy = response.get('camila_strategy', {})
    print(f"\n📈 ESTRATÉGIA APLICADA:")
    print(f"   Segmento: {strategy.get('segmento_identificado')}")
    print(f"   Estratégia: {strategy.get('estrategia_aplicada')}")
    
    # Validações B2B
    resposta_text = response['resposta'].lower()
    b2b_checks = {
        'Menção B2B/Empresarial': any(word in resposta_text for word in ['empresarial', 'corporativo', 'negócio', 'parceiro']),
        'Condições especiais': any(word in resposta_text for word in ['desconto', 'condições', 'especiais', 'volume']),
        'Ação B2B': 'B2B' in (response['acao_especial'] or ''),
        'Tom profissional': 'programa' in resposta_text or 'proposta' in resposta_text
    }
    
    print("\n✅ VALIDAÇÕES B2B:")
    for check, passed in b2b_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    return all(b2b_checks.values())

def test_segmentation_evento():
    """Testa segmentação para eventos especiais"""
    
    print("\n🎉 TESTANDO SEGMENTAÇÃO EVENTOS")
    print("=" * 50)
    
    # Cenário: Evento urgente
    bruno_insights = {
        'segmento': 'evento_especial',
        'lead_score': 9,
        'urgencia': 'alta',
        'pessoas': 40,
        'qualificacao_status': 'hot'
    }
    
    context = {
        'bruno_insights': bruno_insights,
        'cliente': {'telefone': '+5511999997777'}
    }
    
    message = "Preciso de carne para churrasco amanhã, 40 pessoas"
    response = marketing.respond(message, context)
    
    print("📊 ENTRADA:")
    print(f"   Segmento: {bruno_insights['segmento']}")
    print(f"   Urgência: {bruno_insights['urgencia']}")
    print(f"   Pessoas: {bruno_insights['pessoas']}")
    print(f"   Mensagem: '{message}'")
    
    print("\n🎯 RESPOSTA CAMILA:")
    print(f"   {response['resposta'][:150]}...")
    print(f"   Ação: {response['acao_especial']}")
    
    # Validações eventos
    resposta_text = response['resposta'].lower()
    evento_checks = {
        'Reconhece urgência': any(word in resposta_text for word in ['urgente', 'expressa', 'rápid', 'horas']),
        'Menciona evento': any(word in resposta_text for word in ['evento', 'churrasco', 'festa']),
        'Solução específica': any(word in resposta_text for word in ['pacote', 'express', 'premium']),
        'Ação evento': 'EVENTO' in (response['acao_especial'] or ''),
        'Considera pessoas': '40' in response['resposta'] or 'pessoas' in resposta_text
    }
    
    print("\n✅ VALIDAÇÕES EVENTO:")
    for check, passed in evento_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    return all(evento_checks.values())

def test_segmentation_familia():
    """Testa segmentação para pessoa física/família"""
    
    print("\n👨‍👩‍👧‍👦 TESTANDO SEGMENTAÇÃO FAMÍLIA")
    print("=" * 50)
    
    # Cenário: Cliente novo (cold)
    bruno_insights = {
        'segmento': 'pessoa_fisica',
        'lead_score': 3,
        'qualificacao_status': 'cold',
        'urgencia': 'baixa'
    }
    
    context = {
        'bruno_insights': bruno_insights,
        'cliente': {'telefone': '+5511999996666'}
    }
    
    message = "Primeira vez comprando aqui, vocês tem promoção?"
    response = marketing.respond(message, context)
    
    print("📊 ENTRADA:")
    print(f"   Segmento: {bruno_insights['segmento']}")
    print(f"   Status: {bruno_insights['qualificacao_status']}")
    print(f"   Score: {bruno_insights['lead_score']}")
    print(f"   Mensagem: '{message}'")
    
    print("\n🎯 RESPOSTA CAMILA:")
    print(f"   {response['resposta'][:150]}...")
    print(f"   Ação: {response['acao_especial']}")
    
    # Validações família
    resposta_text = response['resposta'].lower()
    familia_checks = {
        'Reconhece primeiro cliente': any(word in resposta_text for word in ['primeira', 'bem-vind', 'novo']),
        'Oferta atrativa': any(word in resposta_text for word in ['desconto', 'promoção', 'oferta', '%']),
        'Tom acolhedor': any(word in resposta_text for word in ['especial', 'preparei', 'você']),
        'Ação conversão': 'BEM_VINDO' in (response['acao_especial'] or '') or 'CLIENTE' in (response['acao_especial'] or ''),
        'Incentiva ação': any(word in resposta_text for word in ['garanto', 'ativamos', 'confirmo'])
    }
    
    print("\n✅ VALIDAÇÕES FAMÍLIA:")
    for check, passed in familia_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    return all(familia_checks.values())

def test_bruno_integration():
    """Testa integração com insights do Bruno"""
    
    print("\n🕵️ TESTANDO INTEGRAÇÃO COM BRUNO")
    print("=" * 50)
    
    # Cenário sem insights do Bruno
    response_sem_bruno = marketing.respond("Tem desconto?")
    
    # Cenário com insights do Bruno
    bruno_insights = {
        'segmento': 'pessoa_fisica',
        'lead_score': 8,
        'qualificacao_status': 'hot',
        'urgencia': 'media',
        'interesse_compra': 9
    }
    
    context_com_bruno = {'bruno_insights': bruno_insights}
    response_com_bruno = marketing.respond("Tem desconto?", context_com_bruno)
    
    print("📊 COMPARAÇÃO SEM vs COM BRUNO:")
    print(f"   Sem Bruno: {len(response_sem_bruno['resposta'])} chars")
    print(f"   Com Bruno: {len(response_com_bruno['resposta'])} chars")
    print(f"   Ação sem Bruno: {response_sem_bruno.get('acao_especial', 'Nenhuma')}")
    print(f"   Ação com Bruno: {response_com_bruno.get('acao_especial', 'Nenhuma')}")
    
    # Verifica se há estratégia aplicada
    strategy = response_com_bruno.get('camila_strategy', {})
    print(f"\n📈 ESTRATÉGIA COM BRUNO:")
    print(f"   Segmento: {strategy.get('segmento_identificado')}")
    print(f"   Estratégia: {strategy.get('estrategia_aplicada')}")
    print(f"   Score: {strategy.get('lead_score')}")
    
    integration_checks = {
        'Usa insights Bruno': 'camila_strategy' in response_com_bruno,
        'Personaliza resposta': len(response_com_bruno['resposta']) > len(response_sem_bruno['resposta']),
        'Ação mais específica': response_com_bruno['acao_especial'] != response_sem_bruno['acao_especial'],
        'Identifica segmento': strategy.get('segmento_identificado') == 'pessoa_fisica'
    }
    
    print("\n✅ VALIDAÇÕES INTEGRAÇÃO:")
    for check, passed in integration_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    return all(integration_checks.values())

def run_complete_test():
    """Executa todos os testes da Camila Marketing"""
    
    print("🚀 INICIANDO TESTE COMPLETO CAMILA MARKETING")
    print("=" * 60)
    
    tests = [
        ("Personalidade", test_camila_personality),
        ("Segmentação B2B", test_segmentation_b2b),
        ("Segmentação Eventos", test_segmentation_evento),
        ("Segmentação Família", test_segmentation_familia),
        ("Integração Bruno", test_bruno_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📝 EXECUTANDO: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ ERRO: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL CAMILA MARKETING")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"✅ Testes passados: {passed}/{total}")
    print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
    
    print(f"\n📋 DETALHES:")
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if success_rate >= 80:
        print(f"\n🎉 CAMILA MARKETING APROVADA!")
        print(f"🚀 Pronta para deploy em produção!")
    else:
        print(f"\n⚠️ Melhorias necessárias antes do deploy")
    
    return success_rate >= 80

if __name__ == '__main__':
    success = run_complete_test()
    exit(0 if success else 1)