import os
import json
import pathlib
from urllib.parse import urlparse
from datetime import datetime, timezone

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# Carrega .env da raiz do projeto
load_dotenv()

# Importa configurações já padronizadas do backend
from server.config import (
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_TOKEN_URI,
    GOOGLE_SCOPES,
    GOOGLE_DRIVE_TOKEN_JSON,
)

# Valores adicionais lidos diretamente do ambiente (não presentes em server.config)
GOOGLE_OAUTH_AUTH_URI = os.getenv("GOOGLE_OAUTH_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8787/")

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _resolve_port_from_redirect(redirect_uri: str | None, fallback_port: int = 8787) -> int:
    if not redirect_uri:
        return fallback_port
    try:
        parsed = urlparse(redirect_uri)
        if parsed.port:
            return parsed.port
    except Exception:
        pass
    return fallback_port


def _ensure_client_config() -> dict:
    if not (GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET):
        raise SystemExit(
            "Faltam GOOGLE_OAUTH_CLIENT_ID/GOOGLE_OAUTH_CLIENT_SECRET no .env."
        )
    redirect_uri = GOOGLE_OAUTH_REDIRECT_URI or f"http://localhost:8787/"
    return {
        "installed": {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "auth_uri": GOOGLE_OAUTH_AUTH_URI or "https://accounts.google.com/o/oauth2/auth",
            "token_uri": GOOGLE_OAUTH_TOKEN_URI or "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def _save_token(creds, token_path: pathlib.Path) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_type": "Bearer",
        "scope": " ".join(creds.scopes or []),
    }
    # expiry pode ser None dependendo do provider; trata com segurança
    if getattr(creds, "expiry", None):
        try:
            # Garante formato ISO8601 com 'Z'
            exp = creds.expiry
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            data["expiry"] = exp.isoformat().replace("+00:00", "Z")
        except Exception:
            pass

    with token_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    client_config = _ensure_client_config()
    scopes = GOOGLE_SCOPES or DEFAULT_SCOPES

    # Determina porta com base no redirect URI (ou 8787 por padrão)
    redirect_uri = client_config["installed"]["redirect_uris"][0]
    port = _resolve_port_from_redirect(redirect_uri, fallback_port=8787)

    flow = InstalledAppFlow.from_client_config(client_config, scopes=scopes)
    creds = flow.run_local_server(
        host="localhost",
        port=port,
        authorization_prompt_message="Abrindo o navegador para autorizar acesso ao Google...",
        success_message="Autorizado com sucesso. Pode fechar esta aba.",
        open_browser=True,
        access_type="offline",  # garante refresh_token
        prompt="consent",       # força consentimento para obter refresh_token
    )

    token_path = pathlib.Path(GOOGLE_DRIVE_TOKEN_JSON).resolve()
    _save_token(creds, token_path)

    print("\n[OK] Token salvo em:", str(token_path))
    print("Scopes:", " ".join(scopes))
    print("Refresh token presente:", bool(creds.refresh_token))


if __name__ == "__main__":
    main()