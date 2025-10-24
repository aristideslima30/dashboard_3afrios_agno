#!/usr/bin/env python3
"""
Teste das melhorias da Sofia - Agente de Catálogo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.agents.catalog import respond, _get_product_keywords, _suggest_quantity, _build_commercial_response

def test_sofia_improvements():
    """Testa as melhorias da Sofia"""
    
    print("=== TESTE DA SOFIA - AGENTE DE CATALOGO MELHORADO ===\n")
    
    # Contexto de teste simulando produtos do Google Sheets
    produtos_teste = [
        {'descricao': 'Picanha Premium', 'preco': '45.90'},
        {'descricao': 'Frango Caipira', 'preco': '12.90'}, 
        {'descricao': 'Linguica Calabresa', 'preco': '18.90'},
        {'descricao': 'Queijo Mussarela', 'preco': '28.90'},
        {'descricao': 'Presunto Cozido', 'preco': '24.90'},
    ]
    
    context_com_produtos = {
        'catalog_items': produtos_teste,
        'conversation_history': []
    }
    
    context_primeira_vez = {'catalog_items': produtos_teste, 'conversation_history': []}
    context_conversa_ativa = {
        'catalog_items': produtos_teste,
        'conversation_history': [
            {'mensagem_cliente': 'oi', 'resposta_bot': 'Oi! Eu sou a Sofia...'},
        ]
    }
    
    # Casos de teste
    test_cases = [
        # SAUDACOES
        ("oi", context_primeira_vez, "Saudacao primeira vez", "Sofia se apresenta como especialista"),
        ("bom dia", context_conversa_ativa, "Saudacao conversa ativa", "Sofia retorna amigavelmente"),
        
        # CONSULTAS ESPECIFICAS
        ("vocês tem picanha?", context_com_produtos, "Consulta específica", "Sofia encontra e sugere"),
        ("quanto custa frango?", context_com_produtos, "Pergunta preço", "Sofia informa preço e sugere quantidade"),
        ("tem linguica?", context_com_produtos, "Busca produto", "Sofia encontra e oferece combo"),
        
        # PEDIDO DE CATALOGO
        ("me manda o catalogo", context_com_produtos, "Pedido catálogo", "Sofia apresenta produtos destacados"),
        ("quero ver os produtos", context_com_produtos, "Ver produtos", "Sofia mostra catálogo comercial"),
        
        # PRODUTO NAO ENCONTRADO
        ("voces tem salmao?", context_com_produtos, "Produto inexistente", "Sofia oferece alternativas"),
        
        # SEM PRODUTOS (fallback)
        ("oi", {'conversation_history': []}, "Sem catálogo", "Sofia se apresenta mesmo sem produtos"),
    ]
    
    print("TESTANDO CASOS DE USO:\n")
    
    acertos = 0
    total = len(test_cases)
    
    for i, (mensagem, context, caso, expectativa) in enumerate(test_cases, 1):
        print(f"{i:2d}. CASO: {caso}")
        print(f"    Mensagem: \"{mensagem}\"")
        print(f"    Expectativa: {expectativa}")
        
        try:
            result = respond(mensagem, context)
            resposta = result['resposta']
            acao = result.get('acao_especial')
            
            # Verificacoes especificas da Sofia
            checks = []
            pontos = 0
            
            # Sofia deve sempre se apresentar
            if 'Sofia' in resposta:
                checks.append("OK: Se apresenta como Sofia")
                pontos += 1
            
            # Resposta substancial
            if len(resposta) > 50:
                checks.append("OK: Resposta completa")
                pontos += 1
            
            # Usa emojis de produtos
            if any(emoji in resposta for emoji in ['🥩', '🐔', '🧀', '🌭', '😊']):
                checks.append("OK: Usa emojis apropriados")
                pontos += 1
            
            # Deteccao de acao especial
            if acao and 'catalogo' in caso.lower():
                checks.append(f"OK: Acao detectada: {acao}")
                pontos += 1
            
            # Verificacoes por tipo de caso
            if "consulta específica" in caso.lower() or "pergunta preço" in caso.lower():
                if any(palavra in resposta.lower() for palavra in ['encontrei', 'r$', 'preço']):
                    checks.append("OK: Informa produto/preço")
                    pontos += 1
            
            if "saudacao" in caso.lower():
                if any(palavra in resposta.lower() for palavra in ['especialista', 'produtos', 'ajudar']):
                    checks.append("OK: Apresentacao profissional")
                    pontos += 1
            
            if "catalogo" in caso.lower():
                if any(palavra in resposta.lower() for palavra in ['destaque', 'produtos', 'catálogo']):
                    checks.append("OK: Apresenta catalogo")
                    pontos += 1
            
            if "inexistente" in caso.lower():
                if any(palavra in resposta.lower() for palavra in ['não encontrei', 'verificar', 'alternativa']):
                    checks.append("OK: Trata produto não encontrado")
                    pontos += 1
            
            # Avaliacao geral
            if pontos >= 3:
                acertos += 1
                status = "PASSOU"
            else:
                status = "FALHOU"
            
            print(f"    Status: {status} ({pontos} pontos)")
            print(f"    Resposta: \"{resposta[:120]}{'...' if len(resposta) > 120 else ''}\"")
            print(f"    Checks: {' | '.join(checks)}")
            
        except Exception as e:
            print(f"    ERRO: {e}")
        
        print()
    
    print(f"RESULTADO GERAL: {acertos}/{total} casos passaram ({acertos/total*100:.1f}%)")
    
    # Teste de funcoes auxiliares
    print("\nTESTANDO FUNCOES AUXILIARES:\n")
    
    # Teste de keywords
    keywords1 = _get_product_keywords("voces tem carne de porco?")
    print(f"Keywords 'carne de porco': {keywords1}")
    
    keywords2 = _get_product_keywords("quanto custa frango?")
    print(f"Keywords 'frango': {keywords2}")
    
    # Teste de sugestao de quantidade
    sugestao1 = _suggest_quantity("Picanha Premium")
    print(f"Sugestao picanha: {sugestao1}")
    
    sugestao2 = _suggest_quantity("Presunto Cozido")
    print(f"Sugestao presunto: {sugestao2}")
    
    print("\nResumo: Sofia agora tem personalidade comercial, sugestoes inteligentes e experiencia aprimorada!")

if __name__ == "__main__":
    test_sofia_improvements()