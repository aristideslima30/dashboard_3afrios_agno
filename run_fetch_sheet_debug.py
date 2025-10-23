import os, json, traceback
from datetime import datetime

# Carrega variáveis do .env da raiz
from dotenv import load_dotenv
load_dotenv()

from server.integrations import google_knowledge
from server.config import GOOGLE_DRIVE_TOKEN_JSON, GOOGLE_SHEET_ID

print('\n--- Debug Google Sheets access ---\n')
# 1) token file info
token_path = GOOGLE_DRIVE_TOKEN_JSON
print(f'Token path configured: {token_path!r}')
if token_path and os.path.exists(token_path):
    st = os.stat(token_path)
    print(f'File exists. Size={st.st_size} bytes, mtime={datetime.fromtimestamp(st.st_mtime)}')
else:
    print('Token file not found on disk.')

# 2) try load credentials
try:
    creds = google_knowledge._load_credentials()
    print('Loaded creds:', 'YES' if creds else 'NO')
    if creds:
        try:
            print('Has token:', bool(getattr(creds, 'token', None)))
            print('Has refresh_token:', bool(getattr(creds, 'refresh_token', None)))
            print('Scopes:', getattr(creds, 'scopes', None))
            print('Expired:', getattr(creds, 'expired', None))
        except Exception as e:
            print('Error inspecting creds:', e)
except Exception as e:
    print('Error in _load_credentials:')
    traceback.print_exc()

# 3) try to fetch spreadsheet metadata to detect permissions errors
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

try:
    creds = google_knowledge._load_credentials()
    if not creds:
        print('\nCannot test API call: no credentials loaded.')
    else:
        service = build('sheets', 'v4', credentials=creds)
        print('\nAttempting to get spreadsheet metadata...')
        meta = service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID, fields='properties,title,sheets.properties').execute()
        print('Spreadsheet title:', meta.get('properties', {}).get('title'))
        sheets = meta.get('sheets', [])
        print('Found sheets count:', len(sheets))
        for s in sheets:
            p = s.get('properties', {})
            print('-', p.get('sheetId'), p.get('title'))
except Exception as e:
    print('\nError fetching spreadsheet metadata:')
    traceback.print_exc()

print('\n--- end debug ---\n')
