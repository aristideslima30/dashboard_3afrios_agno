#!/usr/bin/env python3
"""
Script para verificar e configurar webhooks da Evolution API
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

async def check_instance_info():
    """Verifica informações da instância"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        print("❌ Configurações da Evolution API não encontradas nas variáveis de ambiente")
        return
    
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/instance/fetchInstances"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            print(f"Status da consulta de instâncias: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("📱 Instâncias encontradas:")
                for instance in data:
                    print(f"  - Nome: {instance.get('instanceName')}")
                    print(f"    Status: {instance.get('connectionStatus')}")
                    print(f"    Webhook: {instance.get('webhook', {}).get('url', 'Não configurado')}")
                    print(f"    Eventos: {instance.get('webhook', {}).get('events', [])}")
                    print()
            else:
                print(f"❌ Erro ao consultar instâncias: {response.text}")
                
    except Exception as e:
        print(f"❌ Erro ao conectar com Evolution API: {e}")

async def get_webhook_config():
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
            print(f"📊 Status da consulta do webhook: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("🔗 Configuração atual do webhook:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"⚠️  Resposta do webhook: {response.text}")
                
    except Exception as e:
        print(f"❌ Erro ao consultar webhook: {e}")

async def configure_webhook():
    """Configura o webhook com os eventos necessários"""
    if not all([EVOLUTION_BASE_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_ID]):
        return
    
    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/webhook/set/{EVOLUTION_INSTANCE_ID}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    
    # Configuração do webhook com todos os eventos de mensagem
    webhook_config = {
        "url": WEBHOOK_URL,
        "enabled": True,
        "events": [
            "MESSAGES_UPSERT",
            "MESSAGES_UPDATE", 
            "MESSAGES_DELETE",
            "SEND_MESSAGE"
        ]
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=webhook_config)
            print(f"🔧 Status da configuração do webhook: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ Webhook configurado com sucesso!")
                print("📝 Configuração aplicada:")
                print(json.dumps(webhook_config, indent=2, ensure_ascii=False))
            else:
                print(f"❌ Erro ao configurar webhook: {response.text}")
                
    except Exception as e:
        print(f"❌ Erro ao configurar webhook: {e}")

async def main():
    print("🔍 Verificando configuração da Evolution API...\n")
    
    print("=" * 50)
    print("1️⃣ Informações das instâncias:")
    await check_instance_info()
    
    print("=" * 50)
    print("2️⃣ Configuração atual do webhook:")
    await get_webhook_config()
    
    print("=" * 50)
    print("3️⃣ Configurando webhook para receber mensagens:")
    await configure_webhook()
    
    print("=" * 50)
    print("4️⃣ Verificando configuração após mudanças:")
    await get_webhook_config()

if __name__ == "__main__":
    asyncio.run(main())