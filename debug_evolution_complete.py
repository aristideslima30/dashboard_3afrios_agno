#!/usr/bin/env python3
"""
Diagnóstico completo da instância Evolution API
"""

import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID", "")

async def check_instance_status():
    """Verifica status detalhado da instância"""
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/instance/connectionState/{EVOLUTION_INSTANCE_ID}"
    headers = {"apikey": EVOLUTION_API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("📱 Status da conexão:")
                print(f"  - Estado: {data.get('state')}")
                print(f"  - Status: {data.get('statusReason')}")
                return data.get('state') == 'open'
            else:
                print(f"❌ Erro ao verificar status: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def send_test_message():
    """Envia mensagem de teste para o próprio número"""
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE_ID}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    # Envia para o próprio número da instância
    payload = {
        "number": "558882165395",  # Número que aparece nos logs como sender
        "text": "🤖 Teste de mensagem - " + str(asyncio.get_event_loop().time())
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                print("✅ Mensagem de teste enviada!")
                print("📝 Agora verifique se chegou um evento messages.upsert nos logs")
                return True
            else:
                print(f"❌ Erro ao enviar mensagem: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def test_webhook_events():
    """Testa se webhooks estão funcionando corretamente"""
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/webhook/find/{EVOLUTION_INSTANCE_ID}"
    headers = {"apikey": EVOLUTION_API_KEY}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("🔗 Configuração do webhook:")
                print(f"  - URL: {data.get('url')}")
                print(f"  - Enabled: {data.get('enabled')}")
                print(f"  - Events: {data.get('events')}")
                print(f"  - webhookByEvents: {data.get('webhookByEvents')}")
                
                # Verifica se MESSAGES_UPSERT está na lista
                events = data.get('events', [])
                if 'MESSAGES_UPSERT' in events:
                    print("✅ MESSAGES_UPSERT está configurado")
                else:
                    print("❌ MESSAGES_UPSERT NÃO está configurado!")
                    
                return data
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

async def restart_and_reconfigure():
    """Reinicia e reconfigura a instância"""
    print("🔄 Tentando reconfigurar instância...")
    
    # Tenta different endpoints para restart
    restart_endpoints = [
        f"/instance/restart/{EVOLUTION_INSTANCE_ID}",
        f"/instance/{EVOLUTION_INSTANCE_ID}/restart",
    ]
    
    headers = {"apikey": EVOLUTION_API_KEY}
    
    for endpoint in restart_endpoints:
        url = f"{EVOLUTION_BASE_URL.rstrip('/')}{endpoint}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=headers)
                if response.status_code in [200, 201]:
                    print(f"✅ Restart com sucesso via {endpoint}")
                    await asyncio.sleep(15)  # Aguarda reconexão
                    return True
                else:
                    print(f"❌ {endpoint}: {response.text}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    return False

async def main():
    print("🔍 Diagnóstico completo da Evolution API...\n")
    
    print("=" * 60)
    print("1️⃣ Verificando status da instância:")
    connected = await check_instance_status()
    
    print("=" * 60)
    print("2️⃣ Verificando configuração do webhook:")
    webhook_config = await test_webhook_events()
    
    if not connected:
        print("=" * 60)
        print("3️⃣ Tentando reconectar instância:")
        restarted = await restart_and_reconfigure()
        
        if restarted:
            print("⏳ Aguardando reconexão...")
            await asyncio.sleep(10)
            await check_instance_status()
    
    print("=" * 60)
    print("4️⃣ Enviando mensagem de teste:")
    await send_test_message()
    
    print("=" * 60)
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Verifique os logs da Railway para ver se chegou messages.upsert")
    print("2. Se não chegou, o problema é na Evolution API")
    print("3. Se chegou, o problema é no nosso parser")

if __name__ == "__main__":
    asyncio.run(main())