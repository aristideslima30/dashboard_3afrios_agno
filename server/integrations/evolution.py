# módulo: server.integrations.evolution

import httpx
import logging
import json
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


def _normalize_instance_id(s: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9_-]", "", (s or ""))


def _normalize_phone_br(s: str) -> str:
    digits = "".join(ch for ch in str(s or "") if ch.isdigit())
    if not digits:
        return ""
    if digits.startswith("55"):
        return digits
    # Heurística: se parece número nacional (10/11 dígitos), prefixa +55
    if len(digits) in (10, 11):
        return f"55{digits}"
    # Se tiver tamanho >=12 mas sem 55, prefira prefixar para integradores que exigem DDI
    if len(digits) >= 12:
        return f"55{digits}"
    return digits


# função: send_text(telefone: str, texto: str) -> dict
async def send_text(telefone: str, texto: str) -> dict:
    if not EVOLUTION_ENABLED:
        return {"sent": False, "reason": "disabled"}
    if not (EVOLUTION_BASE_URL and EVOLUTION_API_KEY and EVOLUTION_INSTANCE_ID and EVOLUTION_SEND_TEXT_PATH):
        return {"sent": False, "reason": "missing_config"}

    phone = _normalize_phone_br(telefone)
    safe_text = _normalize_ptbr(_fix_mojibake(_sanitize_text(texto)))
    if not phone:
        return {"sent": False, "reason": "invalid_phone"}
    if not safe_text:
        return {"sent": False, "reason": "empty_text"}

    url_base = f"{EVOLUTION_BASE_URL.rstrip('/')}/{EVOLUTION_SEND_TEXT_PATH.lstrip('/')}"

    variants = []

    url_no_instance = url_base
    inst = _normalize_instance_id(EVOLUTION_INSTANCE_ID or "")
    url_with_instance = f"{url_base.rstrip('/')}/{inst}"
    headers_apikey = {"Content-Type": "application/json; charset=utf-8", "apikey": EVOLUTION_API_KEY}
    headers_bearer = {"Content-Type": "application/json; charset=utf-8", "Authorization": f"Bearer {EVOLUTION_API_KEY}"}

    # apikey + instância no path
    variants.append(("apikey_path_text", url_with_instance, headers_apikey, {"number": phone, "text": safe_text}))
    variants.append(("apikey_path_textMessage", url_with_instance, headers_apikey, {"number": phone, "textMessage": {"text": safe_text}}))

    # apikey + sem instância no path
    variants.append(("apikey_path_text_no_instance", url_no_instance, headers_apikey, {"number": phone, "text": safe_text}))
    variants.append(("apikey_path_textMessage_no_instance", url_no_instance, headers_apikey, {"number": phone, "textMessage": {"text": safe_text}}))

    # apikey + instância no corpo
    variants.append(("apikey_body_instance_text", url_no_instance, headers_apikey, {"number": phone, "text": safe_text, "instance": inst}))

    # bearer + instanceId no corpo
    variants.append(("bearer_body_instanceId_text", url_no_instance, headers_bearer, {"number": phone, "text": safe_text, "instanceId": inst}))

    # bearer + instância no path
    variants.append(("bearer_path_instance_text", url_with_instance, headers_bearer, {"number": phone, "text": safe_text}))

    # Variantes com chaves alternativas de destino
    variants.append(("apikey_phone_field", url_no_instance, headers_apikey, {"phone": phone, "text": safe_text, "instance": inst}))
    variants.append(("apikey_to_field", url_no_instance, headers_apikey, {"to": phone, "text": safe_text, "instance": inst}))
    variants.append(("apikey_chatId_field", url_no_instance, headers_apikey, {"chatId": f"{phone}@c.us", "text": safe_text, "instance": inst}))

    # variações com api/v1
    if "/api/" not in EVOLUTION_SEND_TEXT_PATH:
        url_v1_no_instance = f"{EVOLUTION_BASE_URL.rstrip('/')}/api/v1/{EVOLUTION_SEND_TEXT_PATH.lstrip('/')}"
        url_v1_with_instance = f"{url_v1_no_instance.rstrip('/')}/{inst}"
        variants.append(("apikey_v1_path_text", url_v1_with_instance, headers_apikey, {"number": phone, "text": safe_text}))
        variants.append(("apikey_v1_path_text_no_instance", url_v1_no_instance, headers_apikey, {"number": phone, "text": safe_text}))
        variants.append(("bearer_v1_body_instanceId_text", url_v1_no_instance, headers_bearer, {"number": phone, "text": safe_text, "instanceId": inst}))

    def _classify_attempts(attempts: list[dict]) -> str:
        for a in attempts:
            status = a.get("status_code")
            data = a.get("data")
            text = ""
            try:
                if isinstance(data, (dict, list)):
                    text = json.dumps(data, ensure_ascii=False).lower()
                else:
                    text = str(data or "").lower()
            except Exception:
                text = str(data or "")
            if status == 401:
                return "unauthorized"
            if status == 404:
                return "endpoint_not_found"
            if status and int(status) >= 500:
                return "server_error"
            if "invalid" in text and "number" in text:
                return "invalid_number"
            if "instance" in text and ("offline" in text or "not connected" in text or "disconnected" in text):
                return "instance_offline"
        return "unknown"

    async with httpx.AsyncClient(timeout=10) as client:
        attempts = []
        for variant, url, headers, payload in variants:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                ct = resp.headers.get("content-type", "")
                data = resp.json() if ct.startswith("application/json") else {"body": resp.text}
                if 200 <= resp.status_code < 300:
                    return {"sent": True, "status_code": resp.status_code, "data": data, "variant": variant, "url": url}
                attempts.append({"variant": variant, "status_code": resp.status_code, "data": data, "url": url})
            except Exception as e:
                attempts.append({"variant": variant, "error": str(e), "url": url})
        reason = _classify_attempts(attempts)
        try:
            logging.getLogger("3afrios.backend").warning(f"Evolution send failed: reason={reason} attempts={len(attempts)}")
        except Exception:
            pass
        return {"sent": False, "reason": "all_variants_failed", "classification": reason, "attempts": attempts}