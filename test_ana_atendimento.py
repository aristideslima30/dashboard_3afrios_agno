#!/usr/bin/env python3
"""
Teste das melhorias da Ana - Agente de Atendimento
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.agents.atendimento import respond, detect_conversation_type, detect_emotional_context

def test_ana_improvements():
    """Testa as melhorias da Ana"""
    
    print("=== TESTE DA ANA - AGENTE DE ATENDIMENTO MELHORADO ===\n")
    
    # Contexto de teste
    context_primeira_vez = {'conversation_history': []}
    context_conversa_ativa = {
        'conversation_history': [
            {'mensagem_cliente': 'oi', 'resposta_bot': 'Olá! Sou a Ana...'},
            {'mensagem_cliente': 'quanto custa frango?', 'resposta_bot': 'Vou conectar com nosso especialista...'}
        ]
    }
    
    # Casos de teste
    test_cases = [
        # SAUDAÇÕES - Primeira vez
        ("oi", context_primeira_vez, "Saudação primeira vez", "Ana se apresenta e acolhe"),
        ("bom dia", context_primeira_vez, "Saudação manhã primeira vez", "Ana se apresenta profissionalmente"),
        
        # SAUDAÇÕES - Conversa ativa
        ("oi", context_conversa_ativa, "Saudação conversa ativa", "Ana retorna amigavelmente"),
        
        # INFORMAÇÕES DA EMPRESA
        ("qual o horário de funcionamento?", {}, "Horário funcionamento", "Ana informa horários estruturados"),
        ("vocês fazem entrega?", {}, "Informação entrega", "Ana explica prazos e taxas"),
        
        # CONTEXTO EMOCIONAL - Positivo
        ("muito obrigado, excelente atendimento!", {}, "Elogio", "Ana agradece e engaja"),
        ("adorei os produtos de vocês", {}, "Satisfação", "Ana reforça relacionamento"),
        
        # CONTEXTO EMOCIONAL - Negativo  
        ("tive problema com meu pedido", {}, "Reclamação", "Ana demonstra empatia"),
        ("muito insatisfeito com a demora", {}, "Insatisfação", "Ana pede desculpas e resolve"),
        
        # AÇÕES ESPECIAIS
        ("preciso atualizar meu endereço", {}, "Atualizar endereço", "Ana detecta ação especial"),
        ("quero fazer uma troca", {}, "Troca/devolução", "Ana inicia processo"),
        
        # ENCAMINHAMENTOS
        ("vocês tem carne de porco?", {}, "Pergunta produto", "Ana encaminha para Catálogo"),
        ("quanto custa o frango?", {}, "Pergunta preço", "Ana conecta especialista"),
    ]
    
    print("🧪 TESTANDO CASOS DE USO:\n")
    
    for i, (mensagem, context, caso, expectativa) in enumerate(test_cases, 1):
        print(f"{i:2d}. CASO: {caso}")
        print(f"    Mensagem: \"{mensagem}\"")
        print(f"    Expectativa: {expectativa}")
        
        try:
            result = respond(mensagem, context)
            resposta = result['resposta']
            acao = result.get('acao_especial')
            
            # Verificações básicas
            checks = []
            if 'Ana' in resposta:
                checks.append("✅ Se apresenta como Ana")
            else:
                checks.append("❌ Não se apresentou como Ana")
            
            if len(resposta) > 30:
                checks.append("✅ Resposta substancial")
            else:
                checks.append("❌ Resposta muito curta")
            
            if acao:
                checks.append(f"✅ Ação detectada: {acao}")
            
            # Verificações específicas por caso
            if "saudação" in caso.lower() and ("olá" in resposta.lower() or "oi" in resposta.lower()):
                checks.append("✅ Saudação adequada")
            
            if "horário" in caso.lower() and "segunda" in resposta.lower():
                checks.append("✅ Horários informados")
            
            if "entrega" in caso.lower() and ("prazo" in resposta.lower() or "24" in resposta):
                checks.append("✅ Info entrega completa")
            
            if ("elogio" in caso.lower() or "satisfação" in caso.lower()) and ("feliz" in resposta.lower() or "bom" in resposta.lower()):
                checks.append("✅ Resposta positiva adequada")
            
            if ("reclamação" in caso.lower() or "insatisfação" in caso.lower()) and ("desculp" in resposta.lower() or "resolver" in resposta.lower()):
                checks.append("✅ Tratamento empático")
            
            print(f"    Resposta: \"{resposta[:80]}{'...' if len(resposta) > 80 else ''}\"")
            print(f"    Checks: {' | '.join(checks)}")
            
        except Exception as e:
            print(f"    ❌ ERRO: {e}")
        
        print()
    
    # Teste de detecção de contexto
    print("🔍 TESTANDO DETECÇÃO DE CONTEXTO:\n")
    
    context_tests = [
        ("obrigado, excelente!", "positivo"),
        ("problema com pedido", "negativo"), 
        ("urgente, preciso rápido", "urgente"),
        ("oi, tudo bem?", "neutro"),
    ]
    
    for mensagem, esperado in context_tests:
        detectado = detect_emotional_context(mensagem)
        status = "✅" if detectado == esperado else "❌"
        print(f"{status} \"{mensagem}\" → {detectado} (esperado: {esperado})")
    
    print("\n🎯 RESUMO: Ana agora tem personalidade, contexto e inteligência emocional!")

if __name__ == "__main__":
    test_ana_improvements()