#!/usr/bin/env python3
"""
Script para alterar URL do webhook da Evolution API para testar endpoint diferente
"""

import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da Evolution API
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID", "")

# URL do nosso webhook EVOLUTION (não WhatsApp)
WEBHOOK_URL_EVOLUTION = "https://dashboard3afriosagno-production.up.railway.app/evolution/webhook"

async def change_webhook_url():
    """Muda URL do webhook para endpoint /evolution/webhook"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/webhook/set/{EVOLUTION_INSTANCE_ID}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    # Configuração do webhook para endpoint /evolution/webhook
    webhook_config = {
        "url": WEBHOOK_URL_EVOLUTION,
        "enabled": True,
        "events": [
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE"
        ],
        "webhookByEvents": False,
        "webhookBase64": False
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=webhook_config)
            print(f"🔧 Status da mudança do webhook: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ Webhook alterado com sucesso!")
                print("📝 Nova configuração:")
                print(json.dumps(webhook_config, indent=2, ensure_ascii=False))
                return True
            else:
                print(f"❌ Erro ao alterar webhook: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro ao alterar webhook: {e}")
        return False

async def verify_webhook():
    """Verifica configuração atual do webhook"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/webhook/find/{EVOLUTION_INSTANCE_ID}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("🔗 Configuração atual do webhook:")
                print(f"  - URL: {data.get('url')}")
                print(f"  - Enabled: {data.get('enabled')}")
                print(f"  - Events: {data.get('events')}")
                return True
            else:
                print(f"❌ Erro ao verificar webhook: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro ao verificar webhook: {e}")
        return False

async def main():
    print("🔄 Alterando webhook para endpoint /evolution/webhook...\n")
    
    print("=" * 60)
    print("1️⃣ Configuração atual:")
    await verify_webhook()
    
    print("=" * 60)
    print("2️⃣ Alterando URL do webhook:")
    success = await change_webhook_url()
    
    if success:
        print("=" * 60)
        print("3️⃣ Verificando nova configuração:")
        await verify_webhook()
        
        print("=" * 60)
        print("🎉 Teste agora enviando uma mensagem!")
        print("📝 Webhook configurado para: /evolution/webhook")
    else:
        print("❌ Falhou em alterar webhook")

if __name__ == "__main__":
    asyncio.run(main())