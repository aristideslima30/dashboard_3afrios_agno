# imports de módulo
import logging
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
try:
    from server.config import ALLOWED_ORIGINS, PORT
except ImportError:
    from .config import ALLOWED_ORIGINS, PORT
from .agents.orchestrator import handle_message
from .integrations.evolution import send_text
from .integrations.supabase_store import persist_conversation

# após a inicialização do app
app = FastAPI(title="3A Frios Backend", version="0.1.0")

# Configuração básica de logging
logger = logging.getLogger("3afrios.backend")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS habilitado para: {ALLOWED_ORIGINS}")
logger.info(f"Backend iniciado na porta {PORT}")


# função: webhook (endpoint /webhook)
# função: webhook(req: Request)
@app.post("/webhook")
async def webhook(req: Request):
    # Parse robusto do JSON com fallback de encoding
    try:
        try:
            payload = await req.json()
        except Exception:
            raw = await req.body()
            payload = None
            last_txt = None
            for enc in ("utf-8", "latin-1", "cp1252"):
                try:
                    txt = raw.decode(enc, errors="ignore")
                    txt = txt.lstrip("\ufeff").strip()
                    last_txt = txt
                    payload = json.loads(txt)
                    break
                except Exception:
                    pass
            if payload is None:
                excerpt = (last_txt or raw.decode("utf-8", errors="ignore"))[:200]
                logger.error(f"Falha ao decodificar JSON em /webhook. len={len(raw)} excerpt={excerpt!r}")
                return JSONResponse(
                    _json_safe({"ok": False, "error": "JSON inválido", "detail": "Falha ao decodificar corpo", "received_length": len(raw), "excerpt": excerpt}),
                    media_type="application/json; charset=utf-8",
                )
        tel_log = (
            payload.get('telefone')
            or payload.get('telefoneCliente')
            or (payload.get('cliente') or {}).get('telefone')
        )
        logger.info(f"POST /webhook recebido: acao={payload.get('acao')} telefone={tel_log} dryRun={payload.get('dryRun')}")
    except Exception as e:
        logger.error("Falha ao parsear JSON no /webhook", exc_info=True)
        return JSONResponse(_json_safe({"ok": False, "error": "JSON inválido", "detail": str(e)}), media_type="application/json; charset=utf-8")

    # Protege contra erro do orquestrador
    try:
        result = await handle_message(payload)
    except Exception as e:
        logger.error("Falha no orquestrador", exc_info=True)
        return JSONResponse(_json_safe({"ok": False, "error": "orchestrator_failed", "detail": str(e)}), media_type="application/json; charset=utf-8")

    if not isinstance(result, dict):
        logger.error("Resposta inválida do orquestrador: tipo inesperado")
        return JSONResponse(_json_safe({"ok": False, "error": "orchestrator_invalid_response"}), media_type="application/json; charset=utf-8")
    logger.info(f"Resposta orquestrador: agente={result.get('agente_responsavel')} acao_especial={result.get('acao_especial')} dryRun={result.get('dryRun')}")
    try:
        telefone = (result.get("cliente") or {}).get("telefone")
        texto = result.get("resposta_bot")
        if telefone and texto and not result.get("dryRun"):
            evo = await send_text(telefone, texto)
            result["enviado_via_evolution"] = bool(evo.get("sent"))
            result["evolution_status"] = evo
        # Persistência no Supabase (com tolerância a falhas)
        try:
            supa = await persist_conversation(result)
            result["persistencia_supabase"] = supa
        except Exception:
            pass
    except Exception:
        # Mantém a resposta do orquestrador mesmo se falhar envio/persistência
        pass

    # Normaliza saída
    rb = result.get("resposta_bot")
    cc = result.get("contexto_conversa")
    if isinstance(rb, str) and rb:
        result["resposta_bot"] = _normalize_ptbr(rb)
    if isinstance(cc, str) and cc:
        result["contexto_conversa"] = _normalize_ptbr(cc)

    return JSONResponse(_json_safe(result), media_type="application/json; charset=utf-8")


# função: evolution_webhook(req: Request)
@app.post("/evolution/webhook")
async def evolution_webhook(req: Request):
    # Parsing robusto com fallback de encoding
    try:
        try:
            payload = await req.json()
        except Exception:
            raw = await req.body()
            payload = None
            last_txt = None
            for enc in ("utf-8", "latin-1", "cp1252"):
                try:
                    txt = raw.decode(enc, errors="ignore")
                    txt = txt.lstrip("\ufeff").strip()
                    last_txt = txt
                    payload = json.loads(txt)
                    break
                except Exception:
                    pass
            if payload is None:
                excerpt = (last_txt or raw.decode("utf-8", errors="ignore"))[:200]
                logger.error(f"Falha ao decodificar JSON em /evolution/webhook. len={len(raw)} excerpt={excerpt!r}")
                return JSONResponse(
                    _json_safe({"ok": False, "error": "invalid_payload", "detail": "unable_to_decode", "received_length": len(raw), "excerpt": excerpt}),
                    media_type="application/json; charset=utf-8",
                )

        # Usa o primeiro item quando payload agrupa mensagens em lista
        p = payload
        if isinstance(payload, dict) and isinstance(payload.get("messages"), list) and payload["messages"]:
            p = (payload["messages"][0] or {})

        # Fallbacks de campos comuns (inclui formatos aninhados)
        def _extract_phone(p: dict) -> str:
            base = p.get("number") or p.get("from") or p.get("telefone") or p.get("phone") or ""
            if not base:
                key = p.get("key") or {}
                remote = key.get("remoteJid") or p.get("chatId") or p.get("sender") or ""
                if isinstance(remote, str) and "@" in remote:
                    remote = remote.split("@", 1)[0]
                base = remote or ""
            import re
            return re.sub(r"\D", "", str(base or ""))

        def _extract_text(p: dict) -> str:
            t = p.get("text") or p.get("message") or p.get("body") or p.get("mensagem") or p.get("msg")
            if not t:
                msg = p.get("message") or {}
                if isinstance(msg, dict):
                    t = (
                        msg.get("conversation")
                        or (msg.get("extendedTextMessage") or {}).get("text")
                        or (msg.get("ephemeralMessage") or {}).get("message", {}).get("extendedTextMessage", {}).get("text")
                        or (msg.get("listResponseMessage") or {}).get("title")
                        or ""
                    )
            return str(t or "").strip()

        telefone = _extract_phone(p)
        texto = _extract_text(p)

        if isinstance(telefone, str) and "@" in telefone:
            telefone = telefone.split("@", 1)[0]
        import re
        telefone = re.sub(r"\D", "", telefone or "")

        dr = payload.get("dryRun")
        if isinstance(dr, bool):
            dry_run = dr
        elif isinstance(dr, str):
            dry_run = dr.strip().lower() in ("1", "true", "yes", "y", "on", "t")
        elif isinstance(dr, (int, float)):
            dry_run = int(dr) != 0
        else:
            dry_run = False

        logger.info(f"[Evolution] inbound: telefone={telefone} len(texto)={len(texto)} dryRun={dry_run}")

        internal = {
            "acao": "receber-mensagem",
            "mensagem": texto,
            "telefoneCliente": telefone,
            "dryRun": dry_run,
        }

        # Protege contra erro do orquestrador
        try:
            result = await handle_message(internal)
        except Exception as e:
            logger.error("Falha no orquestrador (Evolution)", exc_info=True)
            return JSONResponse(_json_safe({"ok": False, "error": "orchestrator_failed", "detail": str(e)}), media_type="application/json; charset=utf-8")

        # Garante tipo dict
        if not isinstance(result, dict):
            logger.error("Resposta inválida do orquestrador (Evolution): tipo inesperado")
            return JSONResponse(_json_safe({"ok": False, "error": "orchestrator_invalid_response"}), media_type="application/json; charset=utf-8")

        # Normaliza saída
        rb = result.get("resposta_bot")
        cc = result.get("contexto_conversa")
        if isinstance(rb, str) and rb:
            result["resposta_bot"] = _normalize_ptbr(rb)
        if isinstance(cc, str) and cc:
            result["contexto_conversa"] = _normalize_ptbr(cc)

        # Envia resposta via Evolution (primeiro) e persiste no Supabase (depois)
        try:
            telefone_out = (result.get("cliente") or {}).get("telefone") or telefone
            texto_out = result.get("resposta_bot")
            if telefone_out and texto_out and not result.get("dryRun"):
                evo = await send_text(telefone_out, texto_out)
                result["enviado_via_evolution"] = bool(evo.get("sent"))
                result["evolution_status"] = evo
            try:
                supa = await persist_conversation(result)
                result["persistencia_supabase"] = supa
            except Exception:
                pass
        except Exception:
            pass

        return JSONResponse(_json_safe(result), media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error("Falha ao processar payload na /evolution/webhook", exc_info=True)
        return JSONResponse(
            _json_safe({"ok": False, "error": "invalid_payload", "detail": str(e)}),
            media_type="application/json; charset=utf-8",
        )

@app.get("/")
async def root():
    return {
        "ok": True,
        "service": "3A Frios Backend",
        "endpoints": ["/webhook", "/docs"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# função utilitária: _json_safe
def _json_safe(obj, _depth=3):
    if _depth < 0:
        return "**omitted**"
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(x, _depth - 1) for x in obj]
    if isinstance(obj, dict):
        return {str(_json_safe(k, _depth - 1)): _json_safe(v, _depth - 1) for k, v in obj.items()}
    # Tenta Pydantic v2
    try:
        return obj.model_dump()
    except Exception:
        pass
    # Tenta dataclass
    try:
        import dataclasses
        if dataclasses.is_dataclass(obj):
            return {f.name: _json_safe(getattr(obj, f.name), _depth - 1) for f in dataclasses.fields(obj)}
    except Exception:
        pass
    # Último fallback
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return repr(obj)

# função utilitária: _normalize_ptbr
def _normalize_ptbr(s: str) -> str:
    if not isinstance(s, str):
        return ""
    if not s:
        return ""
    import unicodedata
    s = unicodedata.normalize("NFC", s)  # preserva acentuação corretamente
    # Substitui traços largos por hífen simples (opcional; remova se quiser manter "—"/"–")
    s = s.replace("–", "-").replace("—", "-")
    import re
    # Corrige artefatos "â R$" ocasionais
    s = re.sub(r"\s*â+\s*R\$", " - R$", s)
    # Usa vírgula em valores monetários
    s = re.sub(r"(R\$\s*\d+(?:\.\d{3})*)\.(\d{2})", r"\1,\2", s)
    # Espaços e quebras
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    logger.error("Exceção não tratada", exc_info=True)
    safe = _json_safe({"ok": False, "error": "internal_server_error", "detail": str(exc)})
    return JSONResponse(safe, media_type="application/json; charset=utf-8", status_code=500)