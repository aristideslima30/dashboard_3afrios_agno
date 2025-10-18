import os
from dotenv import load_dotenv

load_dotenv()

def _get_bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on", "t"):
        return True
    if s in ("0", "false", "no", "n", "off", "f", ""):
        return False
    try:
        return bool(int(s))
    except Exception:
        return default

EVOLUTION_ENABLED = _get_bool_env("EVOLUTION_ENABLED", False)
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID", "")
EVOLUTION_SEND_TEXT_PATH = os.getenv("EVOLUTION_SEND_TEXT_PATH", "")

OPENAI_ENABLED = _get_bool_env("OPENAI_ENABLED", False)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE", "")

# Integração Google (OAuth Client)
GOOGLE_ENABLED = _get_bool_env("GOOGLE_ENABLED", True)
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_TOKEN_URI = os.getenv("GOOGLE_OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_SCOPES = [s.strip() for s in os.getenv("GOOGLE_SCOPES", "").split(",") if s.strip()]

GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_TAB = os.getenv("GOOGLE_SHEET_TAB", "")
GOOGLE_SHEET_GID = os.getenv("GOOGLE_SHEET_GID", "")
GOOGLE_SHEET_RANGE = os.getenv("GOOGLE_SHEET_RANGE", "A1:Z1000")
GOOGLE_SHEET_TAB_DESC = os.getenv("GOOGLE_SHEET_TAB_DESC", "")
GOOGLE_SHEET_GID_DESC = os.getenv("GOOGLE_SHEET_GID_DESC", "")
GOOGLE_SHEET_TAB_PRECO = os.getenv("GOOGLE_SHEET_TAB_PRECO", "")
GOOGLE_SHEET_GID_PRECO = os.getenv("GOOGLE_SHEET_GID_PRECO", "")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
GOOGLE_DRIVE_TOKEN_JSON = os.getenv("GOOGLE_DRIVE_TOKEN_JSON", "./secrets/google_token.json")

PORT = int(os.getenv("PORT", "7777"))