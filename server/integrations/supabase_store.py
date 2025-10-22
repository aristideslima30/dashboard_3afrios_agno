import os
import time
import httpx
import logging
from ..config import SUPABASE_URL, SUPABASE_SERVICE_ROLE
import typing as _t
from .evolution import _sanitize_text, _fix_mojibake


async def _client() -> httpx.AsyncClient:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    return httpx.AsyncClient(base_url=f"{SUPABASE_URL.rstrip('/')}/rest/v1", headers=headers, timeout=10)


# Funções alteradas: _find_cliente_by_telefone, _create_cliente_stub, _ensure_cliente_id

async def _find_cliente_by_telefone(telefone: str) -> dict | None:
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE):
        return None
    async with await _client() as c:
        # Consulta CANÔNICA: tabela clientes_delivery, coluna telefone
        resp = await c.get("/clientes_delivery", params={"select": "*", "telefone": f"eq.{telefone}", "limit": "1"})
        if 200 <= resp.status_code < 300:
            data = resp.json() or []
            if data:
                return data[0]
        # Fallback tolerante: ilike para casos com formatação divergente
        resp2 = await c.get("/clientes_delivery", params={"select": "*", "telefone": f"ilike.*{telefone}*", "limit": "1"})
        if 200 <= resp2.status_code < 300:
            data2 = resp2.json() or []
            if data2:
                return data2[0]
        return None


async def _create_cliente_stub(telefone: str) -> dict | None:
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE):
        return None
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload_snake = {
        "nome": "Cliente",
        "telefone": telefone,
        "lead_score": 0,
        "lead_status": "novo",
        "created_at": now,
        "updated_at": now,
    }
    async with await _client() as c:
        # INSERÇÃO CANÔNICA: clientes_delivery com coluna telefone
        resp = await c.post("/clientes_delivery", json=[payload_snake])
        if 200 <= resp.status_code < 300:
            data = resp.json() or []
            return data[0] if data else None
        return None


async def _ensure_cliente_id(telefone: str) -> str:
    cliente = await _find_cliente_by_telefone(telefone)
    if not cliente:
        cliente = await _create_cliente_stub(telefone)
    # `id` pode ser inteiro (BIGSERIAL); normaliza para string
    cid = (cliente or {}).get("id")
    return str(cid) if cid is not None else ""


async def persist_conversation(result: dict) -> dict:
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE):
        return {"ok": False, "reason": "supabase_not_configured"}

    telefone = ((result.get("cliente") or {}).get("telefone") or "").strip()
    cliente_id_input = ((result.get("cliente") or {}).get("id"))
    cliente_id = (
        str(cliente_id_input).strip()
        if (cliente_id_input is not None and str(cliente_id_input).strip() != "")
        else (await _ensure_cliente_id(telefone) if telefone else "")
    )
    if not cliente_id:
        return {"ok": False, "reason": "cliente_not_found_or_created"}

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # Normaliza cliente_id para inteiro quando possível, evitando erros de tipo
    cid_val = None
    try:
        cid_val = int(str(cliente_id))
    except Exception:
        cid_val = cliente_id  # mantém como string se não for dígito

    itens = []
    msg_cliente = _fix_mojibake(_sanitize_text(result.get("mensagem_cliente") or ""))
    if msg_cliente:
        itens.append({
            "cliente_id": cid_val,
            "mensagem_cliente": msg_cliente,
            "tipo_mensagem": "texto",
            "agente_responsavel": result.get("agente_responsavel"),
            "acao_especial": result.get("acao_especial"),
            "timestamp": now,
        })
    resp_bot = _fix_mojibake(_sanitize_text(result.get("resposta_bot") or ""))
    if resp_bot:
        itens.append({
            "cliente_id": cid_val,
            "mensagem_cliente": "",
            "resposta_bot": resp_bot,
            "tipo_mensagem": "texto",
            "agente_responsavel": result.get("agente_responsavel"),
            "acao_especial": result.get("acao_especial"),
            "timestamp": now,
        })

    if not itens:
        return {"ok": True, "inserted": 0}

    # Insere item a item com múltiplos fallbacks para tolerar variações de schema
    results = []
    errors = []
    inserted = 0
    async with await _client() as c:
        for item in itens:
            # 1) Padrão completo
            r1 = await c.post("/temp_messages", json=[item])
            if 200 <= r1.status_code < 300:
                inserted += 1
                results.append({"endpoint": "/temp_messages", "schema": "standard", "data": r1.json()})
                continue

            # 1b) Padrão mínimo (sem resposta_bot, apenas campos essenciais)
            item_min = {k: v for k, v in item.items() if k in {"cliente_id", "mensagem_cliente", "tipo_mensagem", "timestamp"}}
            r1b = await c.post("/temp_messages", json=[item_min])
            if 200 <= r1b.status_code < 300:
                inserted += 1
                results.append({"endpoint": "/temp_messages", "schema": "standard_min", "data": r1b.json()})
                continue

            # 2) Alternativo completo (cliente_telefone, mensagem, tipo, created_at)
            alt = {
                "cliente_telefone": telefone,
                "mensagem": item.get("mensagem_cliente") or item.get("resposta_bot") or "",
                "tipo": item.get("tipo_mensagem") or "texto",
                "agente_responsavel": item.get("agente_responsavel"),
                "created_at": item.get("timestamp") or now,
            }
            r2 = await c.post("/temp_messages", json=[alt])
            if 200 <= r2.status_code < 300:
                inserted += 1
                results.append({"endpoint": "/temp_messages", "schema": "alt", "data": r2.json()})
                continue

            # 2b) Alternativo mínimo
            alt_min = {k: v for k, v in alt.items() if k in {"cliente_telefone", "mensagem", "tipo", "created_at"}}
            r2b = await c.post("/temp_messages", json=[alt_min])
            if 200 <= r2b.status_code < 300:
                inserted += 1
                results.append({"endpoint": "/temp_messages", "schema": "alt_min", "data": r2b.json()})
                continue

            # 3) Endpoint com hífen (alt)
            r3 = await c.post("/temp-messages", json=[alt])
            if 200 <= r3.status_code < 300:
                inserted += 1
                results.append({"endpoint": "/temp-messages", "schema": "alt", "data": r3.json()})
                continue

            # 3b) Endpoint com hífen (alt_min)
            r3b = await c.post("/temp-messages", json=[alt_min])
            if 200 <= r3b.status_code < 300:
                inserted += 1
                results.append({"endpoint": "/temp-messages", "schema": "alt_min", "data": r3b.json()})
                continue

            # Acumula erros detalhados por item
            errors.append({
                "item": item,
                "primary": {"status": r1.status_code, "body": r1.text},
                "primary_min": {"status": r1b.status_code, "body": r1b.text},
                "alt": {"status": r2.status_code, "body": r2.text},
                "alt_min": {"status": r2b.status_code, "body": r2b.text},
                "alt_hyphen": {"status": r3.status_code, "body": r3.text},
                "alt_hyphen_min": {"status": r3b.status_code, "body": r3b.text},
            })

    return {"ok": inserted > 0, "inserted": inserted, "results": results, "errors": errors}


async def fetch_recent_messages_by_telefone(telefone: str, limit: int = 10) -> _t.List[dict]:
    """Lê histórico recente de mensagens por telefone, com múltiplos fallbacks de schema."""
    logger = logging.getLogger("3afrios.backend")
    logger.debug(f"[Supabase] Buscando histórico para telefone {telefone}")
    
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE) or not (telefone or "").strip():
        logger.warning("[Supabase] Configuração incompleta ou telefone inválido")
        return []

    # Tenta obter cliente_id para uma consulta mais estável
    try:
        cliente_id = await _ensure_cliente_id(telefone)
    except Exception:
        cliente_id = ""

    async with await _client() as c:
        # 1) Tenta por cliente_id com order desc
        if cliente_id:
            try:
                r = await c.get(
                    "/temp_messages",
                    params={
                        "select": "*",
                        "cliente_id": f"eq.{cliente_id}",
                        "order": "timestamp.desc",
                        "limit": str(limit),
                    },
                )
                if 200 <= r.status_code < 300:
                    data = r.json() or []
                    if data:
                        logger.info(f"[Supabase] Encontradas {len(data)} mensagens para cliente_id={cliente_id}")
                        return data
                else:
                    logger.warning(f"[Supabase] Erro ao buscar mensagens: status={r.status_code}")
            except Exception as e:
                logger.error(f"[Supabase] Erro ao buscar mensagens: {str(e)}", exc_info=True)
        # 2) Fallback por telefone em diferentes colunas
        columns = ["cliente_telefone", "telefone_cliente", "telefoneCliente", "telefone"]
        for col in columns:
            try:
                r2 = await c.get(
                    "/temp_messages",
                    params={
                        "select": "*",
                        col: f"eq.{telefone}",
                        "order": "timestamp.desc",
                        "limit": str(limit),
                    },
                )
                if 200 <= r2.status_code < 300:
                    data2 = r2.json() or []
                    if data2:
                        return data2
            except Exception:
                pass
        # 3) Endpoint com hífen
        try:
            r3 = await c.get(
                "/temp-messages",
                params={
                    "select": "*",
                    "cliente_telefone": f"eq.{telefone}",
                    "order": "created_at.desc",
                    "limit": str(limit),
                },
            )
            if 200 <= r3.status_code < 300:
                data3 = r3.json() or []
                if data3:
                    return data3
        except Exception:
            pass
    return []