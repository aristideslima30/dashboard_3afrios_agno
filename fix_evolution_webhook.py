#!/usr/bin/env python3
"""
Script para configurar webhook DIRETAMENTE na instância da Evolution API
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

# URL do nosso webhook
WEBHOOK_URL = "https://dashboard3afriosagno-production.up.railway.app/whatsapp/webhook"

async def restart_instance():
    """Reinicia a instância para aplicar configurações"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/instance/restart/{EVOLUTION_INSTANCE_ID}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers)
            print(f"🔄 Status do restart da instância: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ Instância reiniciada com sucesso!")
                print("⏳ Aguardando 10 segundos para reconexão...")
                await asyncio.sleep(10)
            else:
                print(f"❌ Erro ao reiniciar instância: {response.text}")
                
    except Exception as e:
        print(f"❌ Erro ao reiniciar instância: {e}")

async def set_webhook_in_instance():
    """Configura webhook usando endpoint correto"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    # Tenta diferentes endpoints conhecidos
    endpoints = [
        f"/instance/webhook/set/{EVOLUTION_INSTANCE_ID}",
        f"/webhook/set/{EVOLUTION_INSTANCE_ID}",
        f"/instance/{EVOLUTION_INSTANCE_ID}/webhook",
        f"/webhook/{EVOLUTION_INSTANCE_ID}",
    ]
    
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    webhook_config = {
        "url": WEBHOOK_URL,
        "enabled": True,
        "events": ["MESSAGES_UPSERT"]
    }
    
    for endpoint in endpoints:
        url = f"{EVOLUTION_BASE_URL.rstrip('/')}{endpoint}"
        print(f"🔧 Tentando configurar webhook em: {endpoint}")
        
        try:
            async with httpx.AsyncClient() as client:
                # Tenta POST
                response = await client.post(url, headers=headers, json=webhook_config)
                print(f"   POST {response.status_code}: {response.text[:200]}")
                
                if response.status_code in [200, 201]:
                    print(f"✅ Webhook configurado com sucesso via POST {endpoint}!")
                    return True
                
                # Tenta PUT se POST falhar
                response = await client.put(url, headers=headers, json=webhook_config)
                print(f"   PUT {response.status_code}: {response.text[:200]}")
                
                if response.status_code in [200, 201]:
                    print(f"✅ Webhook configurado com sucesso via PUT {endpoint}!")
                    return True
                    
        except Exception as e:
            print(f"   ❌ Erro em {endpoint}: {e}")
    
    return False

async def check_instance_detailed():
    """Verifica detalhes da instância após configuração"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/instance/fetchInstances"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for instance in data:
                    if instance.get('instanceName') == EVOLUTION_INSTANCE_ID:
                        print("📱 Detalhes da instância após configuração:")
                        print(f"  - Nome: {instance.get('instanceName')}")
                        print(f"  - Status: {instance.get('connectionStatus')}")
                        webhook = instance.get('webhook', {})
                        print(f"  - Webhook URL: {webhook.get('url', 'Não configurado')}")
                        print(f"  - Webhook Enabled: {webhook.get('enabled', False)}")
                        print(f"  - Eventos: {webhook.get('events', [])}")
                        break
                        
    except Exception as e:
        print(f"❌ Erro ao verificar instância: {e}")

async def main():
    print("🔧 Configurando webhook DIRETAMENTE na instância...\n")
    
    print("=" * 60)
    print("1️⃣ Reiniciando instância para limpar configurações:")
    await restart_instance()
    
    print("=" * 60)
    print("2️⃣ Configurando webhook na instância:")
    success = await set_webhook_in_instance()
    
    if success:
        print("=" * 60)
        print("3️⃣ Verificando configuração aplicada:")
        await check_instance_detailed()
        
        print("=" * 60)
        print("🎉 Configuração concluída!")
        print("📝 Agora teste enviando uma mensagem no WhatsApp")
    else:
        print("❌ Falhou em configurar webhook em todos os endpoints testados")

if __name__ == "__main__":
    asyncio.run(main())