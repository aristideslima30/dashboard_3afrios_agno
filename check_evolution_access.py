#!/usr/bin/env python3
"""
Script para acessar interface da Evolution API e verificar QR Code
"""

import os
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID", "")

def main():
    print("🔍 Informações para acessar Evolution API:\n")
    
    print("📋 Dados da Evolution API:")
    print(f"  🌐 URL Base: {EVOLUTION_BASE_URL}")
    print(f"  🔑 API Key: {EVOLUTION_API_KEY}")
    print(f"  📱 Instance ID: {EVOLUTION_INSTANCE_ID}")
    
    print("\n🔗 URLs úteis:")
    print(f"  📊 Painel Admin: {EVOLUTION_BASE_URL}/manager")
    print(f"  📱 Status da Instância: {EVOLUTION_BASE_URL}/instance/connect/{EVOLUTION_INSTANCE_ID}")
    print(f"  🔧 Documentação: {EVOLUTION_BASE_URL}/docs")
    
    print("\n📝 PRÓXIMOS PASSOS:")
    print("1. Acesse o painel admin da Evolution")
    print("2. Localize a instância 'chat_3afrios'")
    print("3. Verifique se está conectada ao WhatsApp")
    print("4. Se não estiver, escaneie o QR Code")
    print("5. Teste enviando mensagem novamente")
    
    print("\n⚠️  ATENÇÃO:")
    print("- A instância precisa estar CONECTADA (status 'open')")
    print("- O QR Code pode ter expirado")
    print("- Pode precisar reautenticar no WhatsApp")

if __name__ == "__main__":
    main()