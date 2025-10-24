#!/usr/bin/env python3
"""
Teste das melhorias do orquestrador
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.agents.orchestrator import _score_intent, AgentContext, SmartOrchestrator

def test_routing_improvements():
    """Testa as melhorias de roteamento"""
    
    # Casos de teste
    test_cases = [
        # PEDIDOS (deve detectar intenção de compra)
        ("quero um quilo de carne", "Pedidos", "intenção + quantidade + produto"),
        ("vou querer 2kg de frango", "Pedidos", "intenção + quantidade + produto"), 
        ("me vende uma linguiça", "Pedidos", "verbo de compra + produto"),
        ("preciso de 500g de queijo", "Pedidos", "necessidade + quantidade + produto"),
        ("eu vou levar esse presunto", "Pedidos", "verbo de ação + produto"),
        
        # CATÁLOGO (perguntas sobre produtos)
        ("vocês tem carne de porco?", "Catálogo", "pergunta sobre produto"),
        ("que tipos de queijo vocês vendem?", "Catálogo", "pergunta sobre variedades"),
        ("quanto custa o frango?", "Catálogo", "pergunta sobre preço"),
        ("me manda o catálogo", "Catálogo", "solicitação explícita de catálogo"),
        ("quais carnes vocês trabalham?", "Catálogo", "pergunta sobre produtos"),
        
        # ATENDIMENTO (geral)
        ("oi, tudo bem?", "Atendimento", "saudação"),
        ("qual o horário de funcionamento?", "Atendimento", "informação geral"),
        ("onde vocês ficam?", "Atendimento", "localização"),
    ]
    
    print("=== TESTE DE ROTEAMENTO INTELIGENTE ===\n")
    
    acertos = 0
    total = len(test_cases)
    
    for i, (mensagem, esperado, descricao) in enumerate(test_cases, 1):
        intent, score, terms = _score_intent(mensagem)
        confidence = min(score * 0.25, 1.0)
        
        status = "✅" if intent == esperado else "❌"
        if intent == esperado:
            acertos += 1
        
        print(f"{i:2d}. {status} '{mensagem}'")
        print(f"    Esperado: {esperado} | Obtido: {intent}")
        print(f"    Confiança: {confidence:.2f} | Termos: {terms}")
        print(f"    Contexto: {descricao}")
        print()
    
    print(f"RESULTADO: {acertos}/{total} acertos ({acertos/total*100:.1f}%)")
    
    # Casos especiais para testar detecção de pedidos
    print("\n=== CASOS ESPECIAIS DE PEDIDOS ===")
    
    casos_pedido = [
        "eu vou querer um quilo",  # Antes ia para Catálogo
        "me vende 2kg",
        "quero comprar frango",
        "vou levar uma linguiça",
    ]
    
    for caso in casos_pedido:
        intent, score, terms = _score_intent(caso)
        confidence = min(score * 0.25, 1.0)
        status = "✅ PEDIDO" if intent == "Pedidos" else f"❌ {intent}"
        print(f"{status} | '{caso}' | conf: {confidence:.2f}")


if __name__ == "__main__":
    test_routing_improvements()