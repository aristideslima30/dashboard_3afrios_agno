import os, json, traceback
from datetime import datetime

from server.integrations import google_knowledge
from server.config import GOOGLE_DOC_ID, GOOGLE_SHEET_ID

print('\n--- Testando acesso Docs vs Sheets ---\n')

# Testa Docs
print('1. Tentando buscar documento do Google Docs...')
try:
    doc_text = google_knowledge.fetch_doc_text(GOOGLE_DOC_ID, max_chars=500)
    if doc_text:
        print(f'✓ Documento acessado! Primeiros 200 chars:\n{doc_text[:200]}...\n')
    else:
        print('✗ Documento retornou vazio\n')
except Exception as e:
    print(f'✗ Erro ao acessar Docs:\n{traceback.format_exc()}\n')

# Testa Sheets
print('2. Tentando buscar planilha do Google Sheets...')
try:
    catalog = google_knowledge.fetch_sheet_catalog(GOOGLE_SHEET_ID, max_items=5)
    if catalog['items']:
        print(f'✓ Planilha acessada! Items: {len(catalog["items"])}')
        print(f'Headers: {catalog["headers"]}')
        print(f'Preview:\n{catalog["preview"][:200]}\n')
    else:
        print(f'✗ Planilha retornou vazia')
        print(f'Headers retornados: {catalog["headers"]}')
        print(f'Preview: {catalog["preview"]}\n')
except Exception as e:
    print(f'✗ Erro ao acessar Sheets:\n{traceback.format_exc()}\n')

print('--- Verificando permissões dos arquivos ---\n')

# Testa se os arquivos estão compartilhados publicamente
from googleapiclient.discovery import build

try:
    creds = google_knowledge._load_credentials()
    if creds:
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Checa permissões do Doc
        print('3. Permissões do Documento:')
        doc_perms = drive_service.permissions().list(fileId=GOOGLE_DOC_ID, fields='permissions(id,type,role)').execute()
        for perm in doc_perms.get('permissions', []):
            print(f"  - Tipo: {perm.get('type')}, Role: {perm.get('role')}")
        
        print('\n4. Permissões da Planilha:')
        sheet_perms = drive_service.permissions().list(fileId=GOOGLE_SHEET_ID, fields='permissions(id,type,role)').execute()
        for perm in sheet_perms.get('permissions', []):
            print(f"  - Tipo: {perm.get('type')}, Role: {perm.get('role')}")
            
except Exception as e:
    print(f'Erro ao verificar permissões:\n{traceback.format_exc()}')

print('\n--- Fim do teste ---\n')
