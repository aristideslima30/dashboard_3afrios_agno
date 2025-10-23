#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "server"))

from server.agents.orchestrator import route_to_agent, handle_message
import asyncio

print('=== Testando roteamento ===')

# Teste de roteamento
test_messages = [
    "me mande o catálogo",
    "quanto custa calabresa",
    "vcs tem frango",
    "oi, tudo bem?"
]

for msg in test_messages:
    routing = route_to_agent(msg)
    print(f'Mensagem: "{msg}"')
    print(f'  Intent: {routing["intent"]}, Confidence: {routing["confidence"]}, Terms: {routing.get("matched_terms", [])}')
    print()

print('=== Testando handle_message completo ===')

async def test_handle():
    # Simula um webhook de pedido de catálogo
    payload = {
        'acao': 'responder',
        'mensagem': 'me mande o catálogo',
        'telefone': '11999999999',
        'dryRun': True  # Para não persistir no banco
    }
    
    result = await handle_message(payload)
    print('Payload de entrada:', payload)
    print()
    print('Resultado:')
    print('  Agente:', result.get('agente_responsavel'))
    print('  Routing:', result.get('routing'))
    print('  Resposta (primeiros 200 chars):', result.get('resposta_bot', '')[:200])
    print('  Ação especial:', result.get('acao_especial'))
    print('  OK:', result.get('ok'))

asyncio.run(test_handle())