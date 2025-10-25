#!/usr/bin/env python3
"""
Script para configurar DOIS webhooks - um para cada endpoint
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

async def get_current_webhook():
    """Verifica configuração atual do webhook"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return None
    
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
                return data
            else:
                print(f"❌ Erro ao verificar webhook: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Erro ao verificar webhook: {e}")
        return None

async def test_webhook_endpoints():
    """Testa quais endpoints estão disponíveis"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    # URLs de teste
    test_urls = [
        "https://dashboard3afriosagno-production.up.railway.app/whatsapp/webhook",
        "https://dashboard3afriosagno-production.up.railway.app/evolution/webhook"
    ]
    
    base_config = {
        "enabled": True,
        "events": ["MESSAGES_UPSERT"],
        "webhookByEvents": False,
        "webhookBase64": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    for test_url in test_urls:
        print(f"\n🧪 Testando URL: {test_url}")
        
        config = {**base_config, "url": test_url}
        url = f"{EVOLUTION_BASE_URL.rstrip('/')}/webhook/set/{EVOLUTION_INSTANCE_ID}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=config)
                
                if response.status_code in [200, 201]:
                    print(f"✅ {test_url} - Configurado com sucesso!")
                    
                    # Aguarda um pouco e testa
                    await asyncio.sleep(2)
                    
                    print(f"📋 Enviando mensagem de teste...")
                    # Aqui você poderia enviar uma mensagem de teste
                    
                    # Verifica logs
                    print(f"📝 Agora envie uma mensagem no WhatsApp e vamos ver qual endpoint recebe!")
                    
                    # Aguarda input do usuário
                    input("Pressione Enter após enviar a mensagem...")
                    
                else:
                    print(f"❌ {test_url} - Erro: {response.text}")
                    
        except Exception as e:
            print(f"❌ {test_url} - Exceção: {e}")

async def main():
    print("🔍 Testando diferentes endpoints de webhook...\n")
    
    print("=" * 60)
    print("1️⃣ Configuração atual:")
    current = await get_current_webhook()
    
    print("=" * 60)
    print("2️⃣ Testando endpoints:")
    await test_webhook_endpoints()

if __name__ == "__main__":
    asyncio.run(main())