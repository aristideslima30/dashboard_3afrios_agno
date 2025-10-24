#!/usr/bin/env python3
"""
Teste do Bruno Analista Invisível
Valida análise em background e insights para outros agentes
"""

import re
from typing import Dict, List, Any

# === SIMULAÇÃO DO BRUNO ANALISTA INVISÍVEL ===

def _bruno_analyze_conversation(message: str, conversation_history: List[Dict], context: Dict) -> Dict[str, Any]:
    """
    Bruno Analista Invisível - Qualifica leads silenciosamente em background
    """
    try:
        # Extrai dados da conversa para análise
        recent_messages = [item.get('mensagem_cliente', '') for item in conversation_history[-5:]]
        full_conversation = ' '.join(recent_messages + [message]).lower()
        
        # === ANÁLISE DE PERFIL DO CLIENTE ===
        
        # Detecta segmento
        segmento = 'pessoa_fisica'  # default
        if any(word in full_conversation for word in ['empresa', 'restaurante', 'cnpj', 'corporativo']):
            segmento = 'pessoa_juridica'
        elif any(word in full_conversation for word in ['casamento', 'festa', 'evento', 'formatura']):
            segmento = 'evento_especial'
        
        # Detecta urgência
        urgencia = 'baixa'
        if any(word in full_conversation for word in ['hoje', 'amanhã', 'urgente', 'rápido']):
            urgencia = 'alta'
        elif any(word in full_conversation for word in ['semana', 'próxima']):
            urgencia = 'media'
        
        # Detecta interesse de compra
        interesse_compra = 0
        if any(word in full_conversation for word in ['quero', 'preciso', 'vou levar', 'comprar']):
            interesse_compra += 3
        if any(word in full_conversation for word in ['quanto', 'preço', 'valor', 'custa']):
            interesse_compra += 2
        if any(word in full_conversation for word in ['produto', 'catálogo', 'tem']):
            interesse_compra += 1
            
        # Detecta quantidade de pessoas
        pessoas = None
        pessoas_match = re.search(r'(\d+)\s*pessoas?', full_conversation)
        if pessoas_match:
            pessoas = int(pessoas_match.group(1))
        
        # === SCORE DO LEAD ===
        lead_score = min(10, interesse_compra)
        if urgencia == 'alta':
            lead_score += 2
        if segmento == 'pessoa_juridica':
            lead_score += 1
        if pessoas and pessoas > 20:
            lead_score += 1
            
        # === INSIGHTS PARA OS AGENTES ===
        insights = {
            'lead_score': lead_score,
            'segmento': segmento,
            'urgencia': urgencia,
            'interesse_compra': interesse_compra,
            'pessoas': pessoas,
            'qualificacao_status': 'hot' if lead_score >= 7 else 'warm' if lead_score >= 4 else 'cold',
            'sugestoes_agente': []
        }
        
        # Sugestões específicas por score
        if lead_score >= 7:  # Hot lead
            insights['sugestoes_agente'].append("🔥 LEAD QUENTE - Priorizar fechamento")
            insights['sugestoes_agente'].append("💰 Oferecer condições especiais")
        elif lead_score >= 4:  # Warm lead  
            insights['sugestoes_agente'].append("🌡️ LEAD MORNO - Nutrir interesse")
        else:  # Cold lead
            insights['sugestoes_agente'].append("❄️ LEAD FRIO - Educar sobre produtos")
            
        return insights
        
    except Exception as e:
        print(f"[Bruno Invisible] Erro na análise: {e}")
        return None

def test_bruno_invisible_analyst():
    """Teste do Bruno como analista invisible"""
    
    print("🕵️ TESTANDO BRUNO ANALISTA INVISÍVEL")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Lead Quente - Pedido Urgente',
            'message': 'Quero 2kg de picanha para hoje, quanto fica?',
            'history': [
                {'mensagem_cliente': 'Preciso de carne boa'},
                {'mensagem_cliente': 'É para um churrasco importante'}
            ],
            'expected_status': 'hot',
            'expected_urgencia': 'alta'
        },
        {
            'name': 'Lead Morno - Explorando',
            'message': 'Que produtos vocês tem?',
            'history': [
                {'mensagem_cliente': 'Oi'},
                {'mensagem_cliente': 'Estou vendo opções de carne'}
            ],
            'expected_status': 'warm',
            'expected_urgencia': 'baixa'
        },
        {
            'name': 'Lead Empresarial',
            'message': 'Preciso de fornecedor para meu restaurante',
            'history': [
                {'mensagem_cliente': 'Trabalho com volume mensal'},
                {'mensagem_cliente': 'Empresa de alimentação'}
            ],
            'expected_status': 'warm',
            'expected_segmento': 'pessoa_juridica'
        },
        {
            'name': 'Evento Grande',
            'message': 'Casamento para 80 pessoas, preciso de carnes',
            'history': [
                {'mensagem_cliente': 'Organizando festa'},
                {'mensagem_cliente': 'Evento especial'}
            ],
            'expected_status': 'hot',
            'expected_segmento': 'evento_especial',
            'expected_pessoas': 80
        },
        {
            'name': 'Lead Frio',
            'message': 'Oi',
            'history': [],
            'expected_status': 'cold',
            'expected_urgencia': 'baixa'
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 TESTE {i}: {test['name']}")
        print(f"📝 Mensagem: '{test['message']}'")
        print(f"📚 Histórico: {len(test['history'])} mensagens")
        
        try:
            # Executa análise do Bruno
            insights = _bruno_analyze_conversation(
                test['message'], 
                test['history'], 
                {}
            )
            
            if insights:
                print(f"🎯 Insights Bruno:")
                print(f"   Score: {insights['lead_score']}")
                print(f"   Status: {insights['qualificacao_status']}")
                print(f"   Segmento: {insights['segmento']}")
                print(f"   Urgência: {insights['urgencia']}")
                if insights['pessoas']:
                    print(f"   Pessoas: {insights['pessoas']}")
                print(f"   Sugestões: {insights['sugestoes_agente']}")
                
                # Valida resultados esperados
                success = True
                errors = []
                
                if 'expected_status' in test and insights['qualificacao_status'] != test['expected_status']:
                    success = False
                    errors.append(f"Status esperado: {test['expected_status']}, obtido: {insights['qualificacao_status']}")
                
                if 'expected_urgencia' in test and insights['urgencia'] != test['expected_urgencia']:
                    success = False
                    errors.append(f"Urgência esperada: {test['expected_urgencia']}, obtida: {insights['urgencia']}")
                
                if 'expected_segmento' in test and insights['segmento'] != test['expected_segmento']:
                    success = False
                    errors.append(f"Segmento esperado: {test['expected_segmento']}, obtido: {insights['segmento']}")
                
                if 'expected_pessoas' in test and insights['pessoas'] != test['expected_pessoas']:
                    success = False
                    errors.append(f"Pessoas esperadas: {test['expected_pessoas']}, obtidas: {insights['pessoas']}")
                
                if success:
                    print("✅ SUCESSO!")
                    success_count += 1
                else:
                    print("❌ FALHA!")
                    for error in errors:
                        print(f"   {error}")
            else:
                print("❌ ERRO: Bruno não gerou insights")
                
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
    
    # Relatório final
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL - BRUNO ANALISTA INVISÍVEL")
    print("=" * 50)
    
    print(f"✅ Testes bem-sucedidos: {success_count}/{len(test_cases)}")
    print(f"📈 Taxa de sucesso: {(success_count/len(test_cases)*100):.1f}%")
    
    if success_count == len(test_cases):
        print("\n🎉 PERFEITO! Bruno Analista Invisível funcionando!")
        print("🕵️ Pronto para analisar leads em background!")
    else:
        print(f"\n⚠️ {len(test_cases)-success_count} testes falharam")
    
    # Demonstração de insights para agentes
    print("\n🤖 DEMONSTRAÇÃO DE INSIGHTS PARA AGENTES")
    print("-" * 40)
    
    example_insights = _bruno_analyze_conversation(
        "Quero 3kg de picanha para festa de 25 pessoas amanhã", 
        [{'mensagem_cliente': 'Preciso urgente de carnes boas'}], 
        {}
    )
    
    if example_insights:
        print("📋 Exemplo de insights que Bruno envia para Ana, Sofia e Roberto:")
        print(f"   🎯 Lead Score: {example_insights['lead_score']}/10")
        print(f"   🔥 Status: {example_insights['qualificacao_status'].upper()}")
        print(f"   👥 Pessoas: {example_insights['pessoas'] or 'Não detectado'}")
        print(f"   ⚡ Urgência: {example_insights['urgencia'].upper()}")
        print(f"   🏢 Segmento: {example_insights['segmento']}")
        print("   💡 Sugestões para agentes:")
        for sugestao in example_insights['sugestoes_agente']:
            print(f"      • {sugestao}")
    
    print("\n🏆 BRUNO ANALISTA INVISÍVEL IMPLEMENTADO!")
    
    return success_count == len(test_cases)

if __name__ == '__main__':
    success = test_bruno_invisible_analyst()
    exit(0 if success else 1)