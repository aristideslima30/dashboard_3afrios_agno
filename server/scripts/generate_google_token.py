"""
Script auxiliar para gerar/atualizar o token OAuth do Google (Installed App flow).
Uso local:
  1. Configure as variáveis de ambiente em .env (GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET)
  2. Rode: python server/scripts/generate_google_token.py
  3. Siga o link gerado, autorize, cole o código (se usar run_console) ou o browser redirecionará.

O script grava o arquivo secrets/google_token.json e também imprime o JSON para ser colado na variável
GOOGLE_DRIVE_TOKEN do Railway (caso queira).

Observação: Este fluxo é para credenciais do tipo "Desktop" / Installed App. Se você preferir usar
uma Service Account para produção, me avise que eu adiciono suporte ao método com chave de conta de serviço.
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes padrão
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
TOKEN_PATH = os.getenv("GOOGLE_DRIVE_TOKEN_JSON", str(Path(__file__).parents[1] / "secrets" / "google_token.json"))

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERRO: defina GOOGLE_OAUTH_CLIENT_ID e GOOGLE_OAUTH_CLIENT_SECRET no seu ambiente (.env)")
    raise SystemExit(1)

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

print("Iniciando fluxo de autorização do Google (InstalledAppFlow)...")
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

# Cria pasta secrets se necessário
token_file = Path(TOKEN_PATH)
if not token_file.parent.exists():
    token_file.parent.mkdir(parents=True, exist_ok=True)

# Serializa token mínimo (compatível com _load_credentials)
token_data = {
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "scope": " ".join(creds.scopes or []),
    "token_type": "Bearer",
}

with open(token_file, "w", encoding="utf-8") as f:
    json.dump(token_data, f, ensure_ascii=False, indent=2)

print(f"Token salvo em: {token_file}")
print("\n--- Copie o JSON abaixo e cole na variável GOOGLE_DRIVE_TOKEN no Railway (se desejar):\n")
print(json.dumps(token_data, ensure_ascii=False, indent=2))
print("\nPronto. Agora o backend deve conseguir acessar Docs/Sheets/Drive.")
