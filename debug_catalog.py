#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "server"))

from server.integrations.google_knowledge import fetch_sheet_catalog, build_context_for_intent
from server.config import GOOGLE_SHEET_ID

print('=== Testando fetch da planilha ===')
catalog = fetch_sheet_catalog(GOOGLE_SHEET_ID, max_items=5)
print(f'Items encontrados: {len(catalog.get("items", []))}')
print(f'Headers: {catalog.get("headers", [])}')
if catalog.get('items'):
    print('Primeiro item:')
    print(catalog['items'][0])
else:
    print('PROBLEMA: Nenhum item encontrado!')
    print('Retorno completo:', catalog)

print('\n=== Testando contexto para Catálogo ===')
ctx = build_context_for_intent('Catálogo')
print(f'catalog_items no contexto: {len(ctx.get("catalog_items", []))}')
if ctx.get('catalog_items'):
    print('Primeiro item do contexto:')
    print(ctx['catalog_items'][0])
else:
    print('PROBLEMA: Nenhum item no contexto!')

print('\n=== Testando agente Catálogo ===')
from server.agents.catalog import respond

# Teste 1: pedido de catálogo
result1 = respond("me mande o catálogo", context=ctx)
print('Teste 1 - "me mande o catálogo":')
print('Resposta:', result1['resposta'][:200] + '...' if len(result1['resposta']) > 200 else result1['resposta'])
print('Ação especial:', result1.get('acao_especial'))

# Teste 2: pergunta específica
result2 = respond("quanto custa calabresa", context=ctx)
print('\nTeste 2 - "quanto custa calabresa":')
print('Resposta:', result2['resposta'][:200] + '...' if len(result2['resposta']) > 200 else result2['resposta'])
print('Ação especial:', result2.get('acao_especial'))