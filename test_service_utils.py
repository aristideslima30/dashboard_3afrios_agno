#!/usr/bin/env python3
"""
Teste das ferramentas do Service refatorado
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.agents.service import get_service_utils

def test_service_utils():
    """Testa todas as ferramentas do Service"""
    service = get_service_utils()
    
    print("🔧 Testando Ferramentas do Service Utils")
    print("=" * 50)
    
    # Teste 1: Validação de telefone
    print("\n📞 Teste de Validação de Telefone:")
    telefones = ["11987654321", "(11) 9 8765-4321", "11 98765-4321", "1234"]
    for tel in telefones:
        result = service.validar_telefone(tel)
        print(f"  {tel} -> {result}")
    
    # Teste 2: Validação de CEP
    print("\n📍 Teste de Validação de CEP:")
    ceps = ["01234-567", "01234567", "12345", "abcde-fgh"]
    for cep in ceps:
        result = service.validar_cep(cep)
        print(f"  {cep} -> {result}")
    
    # Teste 3: Cálculo de prazo de entrega
    print("\n🚚 Teste de Cálculo de Prazo:")
    ceps_teste = ["01234-567", "20000-000", "30000-000", "60000-000"]
    for cep in ceps_teste:
        result = service.calcular_prazo_entrega(cep, peso_kg=2.5)
        print(f"  CEP {cep} (2.5kg) -> {result}")
    
    # Teste 4: Formatação de endereço
    print("\n🏠 Teste de Formatação de Endereço:")
    endereco = {
        "logradouro": "Rua das Flores",
        "numero": "123", 
        "complemento": "Apto 45",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": "01234567"
    }
    result = service.formatar_endereco(endereco)
    print(f"  Endereço formatado:\n{result}")
    
    # Teste 5: Validação de dados do cliente
    print("\n👤 Teste de Validação de Cliente:")
    dados_cliente = {
        "telefone": "11987654321",
        "cep": "01234-567",
        "logradouro": "Rua das Flores",
        "numero": "123",
        "cidade": "São Paulo",
        "uf": "SP"
    }
    result = service.validar_dados_cliente(dados_cliente)
    print(f"  Validação: {result}")
    
    # Teste 6: Formatação monetária
    print("\n💰 Teste de Formatação Monetária:")
    valores = [15.50, 1234.99, 0.50, 10000.00]
    for valor in valores:
        result = service.formatar_valor_monetario(valor)
        print(f"  {valor} -> {result}")
    
    # Teste 7: Extração de quantidades
    print("\n⚖️ Teste de Extração de Quantidades:")
    textos = [
        "Quero 2kg de carne",
        "Preciso de meio quilo de queijo",
        "Vou levar 500g de presunto e 1 litro de leite",
        "Duas unidades de frango",
        "Um quilo e meio de picanha"
    ]
    for texto in textos:
        result = service.extrair_quantidades_texto(texto)
        print(f"  '{texto}' -> {result}")
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    test_service_utils()