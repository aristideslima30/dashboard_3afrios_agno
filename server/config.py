import os
from dotenv import load_dotenv

load_dotenv()

EVOLUTION_ENABLED = bool(int(os.getenv("EVOLUTION_ENABLED", "0")))
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID", "")
EVOLUTION_SEND_TEXT_PATH = os.getenv("EVOLUTION_SEND_TEXT_PATH", "")

OPENAI_ENABLED = bool(int(os.getenv("OPENAI_ENABLED", "0")))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE", "")

# Integração Google (OAuth Client)
GOOGLE_ENABLED = bool(int(os.getenv("GOOGLE_ENABLED", "1")))
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_TOKEN_URI = os.getenv("GOOGLE_OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_SCOPES = [s.strip() for s in os.getenv("GOOGLE_SCOPES", "").split(",") if s.strip()]

GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
# NOVOS: seleção de aba/range do Sheets
GOOGLE_SHEET_TAB = os.getenv("GOOGLE_SHEET_TAB", "")
GOOGLE_SHEET_GID = os.getenv("GOOGLE_SHEET_GID", "")
GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "A1:Z1000")
# Novas variáveis para duas abas
GOOGLE_SHEET_TAB_DESC = os.getenv("GOOGLE_SHEET_TAB_DESC", "")
GOOGLE_SHEET_GID_DESC = os.getenv("GOOGLE_SHEET_GID_DESC", "")
GOOGLE_SHEET_TAB_PRECO = os.getenv("GOOGLE_SHEET_TAB_PRECO", "")
GOOGLE_SHEET_GID_PRECO = os.getenv("GOOGLE_SHEET_GID_PRECO", "")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
GOOGLE_DRIVE_TOKEN_JSON = os.getenv("GOOGLE_DRIVE_TOKEN_JSON", "./secrets/google_token.json")

PORT = int(os.getenv("PORT", "7777"))