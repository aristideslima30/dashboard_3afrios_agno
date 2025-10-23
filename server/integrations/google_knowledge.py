import json
import os
from typing import Dict, Any, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# trecho de imports do módulo
from ..config import (
    GOOGLE_ENABLED,
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_TOKEN_URI,
    GOOGLE_SCOPES,
    GOOGLE_DOC_ID,
    GOOGLE_SHEET_ID,
    GOOGLE_DRIVE_TOKEN_JSON,
    # NOVOS imports
    GOOGLE_SHEET_TAB,
    GOOGLE_SHEET_GID,
    GOOGLE_SHEET_RANGE,
    # Novos para duas abas
    GOOGLE_SHEET_TAB_DESC,
    GOOGLE_SHEET_GID_DESC,
    GOOGLE_SHEET_TAB_PRECO,
    GOOGLE_SHEET_GID_PRECO,
)


def _load_credentials() -> Credentials | None:
    if not GOOGLE_ENABLED:
        return None
    if not (GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET and GOOGLE_OAUTH_TOKEN_URI):
        return None

    # Primeiro tenta ler do arquivo
    token = None
    token_path = GOOGLE_DRIVE_TOKEN_JSON
    if os.path.exists(token_path):
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                token = json.load(f)
        except Exception:
            pass
    
    # Se não encontrou arquivo, tenta ler da variável de ambiente
    if not token:
        token_json = os.getenv("GOOGLE_DRIVE_TOKEN")
        if token_json:
            try:
                token = json.loads(token_json)
            except Exception:
                pass
    
    if not token:
        return None

    creds = Credentials(
        token=token.get("access_token"),
        refresh_token=token.get("refresh_token"),
        token_uri=GOOGLE_OAUTH_TOKEN_URI,
        client_id=GOOGLE_OAUTH_CLIENT_ID,
        client_secret=GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=GOOGLE_SCOPES or [
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Opcional: persiste novo access_token no mesmo arquivo
            with open(token_path, "w", encoding="utf-8") as f:
                json.dump({
                    "access_token": creds.token,
                    "refresh_token": token.get("refresh_token"),
                    "scope": " ".join(creds.scopes or []),
                    "token_type": "Bearer",
                }, f)
        except Exception:
            pass

    return creds


def fetch_doc_text(doc_id: str | None = None, max_chars: int = 4000) -> str:
    if not doc_id:
        return ""
    creds = _load_credentials()
    if not creds:
        return ""
    service = build("docs", "v1", credentials=creds)
    doc = service.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])

    def _extract_text(elements: List[dict]) -> str:
        buf: List[str] = []
        for e in elements:
            p = e.get("paragraph")
            if not p:
                continue
            for r in (p.get("elements") or []):
                tr = r.get("textRun")
                if tr and tr.get("content"):
                    buf.append(tr.get("content"))
        return "".join(buf)

    text = _extract_text(content)
    text = (text or "").strip()
    return text[:max_chars]


# função fetch_sheet_catalog
from ..config import (
    GOOGLE_SHEET_ID,
    GOOGLE_DRIVE_TOKEN_JSON,
    # NOVOS imports
    GOOGLE_SHEET_TAB,
    GOOGLE_SHEET_GID,
    GOOGLE_SHEET_RANGE,
)

def fetch_sheet_catalog(sheet_id: str | None = None, value_range: str | None = None, max_items: int = 15) -> Dict[str, Any]:
    if not sheet_id:
        return {"items": [], "headers": [], "preview": ""}
    creds = _load_credentials()
    if not creds:
        return {"items": [], "headers": [], "preview": ""}
    service = build("sheets", "v4", credentials=creds)

    rng = (value_range or GOOGLE_SHEET_RANGE or "A1:Z1000").strip()

    def _resolve_title_by_gid(gid: str) -> str:
        if not gid:
            return ""
        try:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets(properties(sheetId,title))",
            ).execute()
            for s in meta.get("sheets", []):
                p = s.get("properties", {})
                if str(p.get("sheetId")) == str(gid):
                    return p.get("title", "")
        except Exception:
            pass
        return ""

    def _to_dicts(values: List[List[str]]) -> tuple[list[str], list[dict]]:
        if not values:
            return [], []
        # Detecta automaticamente a primeira linha "não vazia" como cabeçalho
        header_idx = None
        for i, row in enumerate(values[:10]):
            if any(str(c).strip() for c in row or []):
                header_idx = i
                break
        if header_idx is None:
            return [], []
        headers = [str(h).strip() for h in (values[header_idx] or [])]
        rows = []
        for row in values[header_idx + 1:]:
            if not any(str(c).strip() for c in row or []):
                continue
            d = {}
            for i, h in enumerate(headers):
                d[str(h).lower()] = (row[i] if i < len(row) else "")
            rows.append(d)
        return headers, rows

    def _pick(d: dict, keys: list[str]) -> str:
        for k in keys:
            v = d.get(k)
            if v:
                return str(v).strip()
        return ""

    # Checa configuração de duas abas
    desc_tab = (GOOGLE_SHEET_TAB_DESC or _resolve_title_by_gid(GOOGLE_SHEET_GID_DESC)).strip()
    preco_tab = (GOOGLE_SHEET_TAB_PRECO or _resolve_title_by_gid(GOOGLE_SHEET_GID_PRECO)).strip()

    if desc_tab and preco_tab:
        try:
            res_desc = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{desc_tab}!{rng}",
            ).execute()
            # Fallback: ler a aba inteira se vier vazio
            if not res_desc.get("values"):
                res_desc = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=desc_tab,
                ).execute()

            res_preco = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{preco_tab}!{rng}",
            ).execute()
            if not res_preco.get("values"):
                res_preco = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=preco_tab,
                ).execute()
        except Exception:
            return {"items": [], "headers": [], "preview": ""}

        headers_desc, rows_desc = _to_dicts(res_desc.get("values", []))
        headers_preco, rows_preco = _to_dicts(res_preco.get("values", []))

        name_keys = ["produto", "nome", "item", "descrição", "descricao"]
        desc_keys = ["descrição", "descricao", "detalhe", "observação"]
        price_keys = ["preço", "preco", "valor", "price"]

        def _norm(s: str) -> str:
            return (s or "").strip().lower()

        map_desc: dict[str, dict] = {}
        for r in rows_desc:
            nome = _pick(r, name_keys)
            if not nome:
                continue
            map_desc[_norm(nome)] = {
                "produto": nome,
                "descricao": _pick(r, desc_keys),
            }

        map_preco: dict[str, dict] = {}
        for r in rows_preco:
            nome = _pick(r, name_keys)
            if not nome:
                continue
            map_preco[_norm(nome)] = {
                "produto": nome,
                "preco": _pick(r, price_keys),
            }

        items: list[dict] = []
        for key, d in map_desc.items():
            p = map_preco.get(key, {})
            items.append({
                "produto": d.get("produto", ""),
                "descricao": d.get("descricao", ""),
                "preco": p.get("preco", ""),
            })
        items = [i for i in items if i.get("produto")] [:max_items]

        preview_lines = []
        for it in items:
            nome = it.get("produto", "")
            preco = it.get("preco", "")
            if preco:
                preview_lines.append(f"{nome} — R$ {preco}")
            else:
                preview_lines.append(f"{nome}")
        preview = "\n".join(preview_lines)

        return {"items": items, "headers": list(set(headers_desc + headers_preco)), "preview": preview}

    # Caso contrário, mantém lógica de aba única
    final_range = rng
    if "!" not in rng:
        tab = (GOOGLE_SHEET_TAB or _resolve_title_by_gid(GOOGLE_SHEET_GID)).strip()
        if tab:
            final_range = f"{tab}!{rng}"
    try:
        res = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=final_range,
        ).execute()
        # Fallback: ler a aba inteira se vier vazio
        if not res.get("values") and "!" in final_range:
            tab_only = final_range.split("!")[0]
            res = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=tab_only,
            ).execute()
    except Exception:
        return {"items": [], "headers": [], "preview": ""}

    headers, rows = _to_dicts(res.get("values", []))
    items = rows[:max_items]

    # Detecta as colunas específicas DESCRICAO e PRECO (case-insensitive)
    desc_keys = ["descricao", "descrição", "produto", "nome", "item", "description"]
    price_keys = ["preco", "preço", "valor", "price"]
    
    col_desc = next((h for h in headers if h.lower() in desc_keys), headers[0] if headers else "")
    col_price = next((h for h in headers if h.lower() in price_keys), "")

    preview_lines = []
    for it in items:
        desc = it.get(str(col_desc).lower(), "")
        price = it.get(str(col_price).lower(), "")
        if desc and price:
            preview_lines.append(f"{desc} — R$ {price}")
        elif desc:
            preview_lines.append(desc)
    return {"items": items, "headers": headers, "preview": "\n".join(preview_lines)}


def build_context_for_intent(intent: str) -> Dict[str, Any]:
    import logging
    logger = logging.getLogger("3afrios.backend")
    
    logger.info(f"[GoogleKnowledge] Construindo contexto para intent: {intent}")
    
    identity_text = fetch_doc_text(GOOGLE_DOC_ID, max_chars=2000) if GOOGLE_DOC_ID else ""
    # Usa range/aba configurável e captura itens estruturados
    catalog = (
        fetch_sheet_catalog(GOOGLE_SHEET_ID, value_range=GOOGLE_SHEET_RANGE, max_items=50)
        if GOOGLE_SHEET_ID else {"items": [], "headers": [], "preview": ""}
    )
    
    logger.info(f"[GoogleKnowledge] Catalog fetched - items: {len(catalog.get('items', []))}, preview: {len(catalog.get('preview', ''))}")
    if catalog.get('items'):
        logger.info(f"[GoogleKnowledge] Primeiro item: {catalog['items'][0]}")
    
    ctx: Dict[str, Any] = {
        "identity_text": identity_text,
        "catalog_preview": catalog.get("preview", ""),
        "catalog_items": catalog.get("items", []),
        "catalog_headers": catalog.get("headers", []),
    }

    # Ajuste simples por intenção
    if intent in ("Catálogo", "Pedidos"):
        result = {
            "identity_text": identity_text[:800],
            "catalog_preview": catalog.get("preview", ""),
            "catalog_items": catalog.get("items", [])[:20],
            "catalog_headers": catalog.get("headers", []),
        }
        logger.info(f"[GoogleKnowledge] Contexto para {intent} - items: {len(result['catalog_items'])}")
        return result
    if intent == "Atendimento":
        result = {
            "identity_text": identity_text,
            "catalog_preview": catalog.get("preview", "")[:500],
            "catalog_items": catalog.get("items", [])[:10],
            "catalog_headers": catalog.get("headers", []),
        }
        logger.info(f"[GoogleKnowledge] Contexto para {intent} - items: {len(result['catalog_items'])}")
        return result
    
    logger.info(f"[GoogleKnowledge] Contexto padrão para {intent} - items: {len(ctx['catalog_items'])}")
    return ctx