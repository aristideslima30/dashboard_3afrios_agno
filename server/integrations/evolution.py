# módulo: server.integrations.evolution

import httpx
from ..config import (
    EVOLUTION_ENABLED,
    EVOLUTION_BASE_URL,
    EVOLUTION_API_KEY,
    EVOLUTION_INSTANCE_ID,
    EVOLUTION_SEND_TEXT_PATH,
)

def _sanitize_text(s: str) -> str:
    s = (s or "").replace("\r\n", "\n").replace("\x0b", "\n")
    import re
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()

def _fix_mojibake(s: str) -> str:
    try:
        if any(ch in s for ch in ("Ã", "Â", "¤", "â")):
            return s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        pass
    return s

def _normalize_ptbr(s: str) -> str:
    if not s:
        return ""
    try:
        s = s.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        pass
    s = s.replace("–", "-").replace("—", "-")
    import re
    s = re.sub(r"\s*â+\s*R\$", " - R$", s)
    s = re.sub(r"(R\$\s*\d+(?:\.\d{3})*)\.(\d{2})", r"\1,\2", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return _sanitize_text(s)

async def send_text(telefone: str, texto: str) -> dict:
    if not EVOLUTION_ENABLED:
        return {"sent": False, "reason": "disabled"}
    if not (EVOLUTION_BASE_URL and EVOLUTION_API_KEY and EVOLUTION_INSTANCE_ID and EVOLUTION_SEND_TEXT_PATH):
        return {"sent": False, "reason": "missing_config"}

    url = f"{EVOLUTION_BASE_URL.rstrip('/')}/{EVOLUTION_SEND_TEXT_PATH.lstrip('/')}"
    safe_text = _normalize_ptbr(_fix_mojibake(_sanitize_text(texto)))
    payload = {"number": telefone, "text": safe_text, "instanceId": EVOLUTION_INSTANCE_ID}
    headers = {"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {EVOLUTION_API_KEY}"}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            ok = 200 <= resp.status_code < 300
            data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"body": resp.text}
            return {"sent": ok, "status_code": resp.status_code, "data": data}
        except Exception as e:
            return {"sent": False, "error": str(e)}