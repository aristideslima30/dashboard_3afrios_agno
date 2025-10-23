# imports de módulo
import logging
import json
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
try:
    from server.config import ALLOWED_ORIGINS as ALLOWED_ORIGINS, PORT
except ImportError:
    from .config import ALLOWED_ORIGINS, PORT
from .agents.orchestrator import handle_message
from .integrations.evolution import send_text
from .integrations.supabase_store import persist_conversation
from .integrations.webhook_parser import parse_incoming_events
from .integrations.google_knowledge import build_context_for_intent

# após a inicialização do app
app = FastAPI(title="3A Frios Backend", version="0.1.0")

# Configuração básica de logging
logger = logging.getLogger("3afrios.backend")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
# Força nível DEBUG para capturar todos os logs
logger.setLevel(logging.DEBUG)
# Configura logging do uvicorn também
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.DEBUG)

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
@app.post("/webhook")
async def webhook(request: Request):
    # Parse robusto do JSON com fallback de encoding
    try:
        try:
            payload = await request.json()
        except Exception:
            raw = await request.body()
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
        texto = payload.get('mensagem', '')
        
        # Verifica duplicação usando cache global (exceto para mensagens manuais)
        if payload.get('acao') != 'responder-manual' and tel_log and texto:
            if _check_global_dedup(tel_log, texto):
                return JSONResponse(_json_safe({"ok": True, "ignored": "duplicate_message", "telefone": tel_log}))
        
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
        texto = result.get("resposta_bot") or result.get("mensagem_cliente")
        if telefone and texto and not result.get("dryRun"):
            evo = await send_text(telefone, texto)
            result["enviado_via_evolution"] = bool(evo.get("sent"))
            result["evolution_status"] = evo

            # Enviar snippet do catálogo quando houver ação especial
            if (result.get("acao_especial") or "").strip() == "[ACAO:ENVIAR_CATALOGO]":
                try:
                    ctx = build_context_for_intent("Catálogo")
                    prev = (ctx.get("catalog_preview") or "").strip()
                    if prev:
                        lines = [l for l in prev.splitlines() if l.strip()]
                        snippet = "\n".join(lines[:12])
                        await send_text(telefone, snippet)
                except Exception:
                    pass
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
async def evolution_webhook(request: Request):
    # Parsing robusto com fallback de encoding
    try:
        try:
            payload = await request.json()
        except Exception:
            body = await request.body()
            try:
                payload = json.loads(body.decode("utf-8", errors="ignore"))
            except Exception:
                payload = {}

        # NEW: detectar eventos fromMe (mensagens do próprio bot) e ignorar
        def _is_from_me(p: dict) -> bool:
            try:
                k = p.get("key") or {}
                return bool(
                    p.get("fromMe") or
                    k.get("fromMe") or
                    (p.get("message") or {}).get("fromMe")
                )
            except Exception:
                return False

        if _is_from_me(payload):
            return JSONResponse({"ok": True, "ignored": "from_me"})

        # Usa o primeiro item quando payload agrupa mensagens em lista
        p = payload
        if isinstance(payload, dict) and isinstance(payload.get("messages"), list) and payload["messages"]:
            p = (payload["messages"][0] or {})

        # NEW: ignorar fromMe também no item da lista (nested)
        if _is_from_me(p):
            return JSONResponse({"ok": True, "ignored": "from_me_nested"})

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
            t = p.get("text") or p.get("body") or p.get("mensagem") or p.get("msg")
            if not t:
                msg = p.get("message") or {}
                if isinstance(msg, dict):
                    t = (
                        msg.get("text")
                        or msg.get("conversation")
                        or (msg.get("extendedTextMessage") or {}).get("text")
                        or (msg.get("textMessage") or {}).get("text")
                        or (msg.get("textMessageData") or {}).get("textMessage")
                        or (msg.get("ephemeralMessage") or {}).get("message", {}).get("extendedTextMessage", {}).get("text")
                        or (msg.get("listResponseMessage") or {}).get("title")
                        or ""
                    )
            if not t and isinstance(p.get("textMessage"), dict):
                tm = p.get("textMessage") or {}
                t = tm.get("text") or tm.get("textMessage") or ""
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

        # NEW: event_id para debug/dedupe básico
        event_id = (
            ((p.get("key") or {}).get("id")) or
            p.get("id") or
            ((payload.get("key") or {}).get("id")) or
            payload.get("id") or
            f"evt-{int(time.time() * 1000)}"
        )

        # NEW: dedupe simples em memória com TTL (event_id + msg)
        try:
            _DEDUP_EVENT_CACHE  # type: ignore
        except NameError:
            _DEDUP_EVENT_CACHE = {}  # type: ignore

        try:
            _DEDUP_MSG_CACHE  # type: ignore
        except NameError:
            _DEDUP_MSG_CACHE = {}  # type: ignore

        now = time.time()
        ttl_seconds = DEDUPE_TTL_SECONDS

        # prune expirados (event_id)
        for k, exp in list(_DEDUP_EVENT_CACHE.items()):  # type: ignore
            if exp < now:
                _DEDUP_EVENT_CACHE.pop(k, None)  # type: ignore

        # prune expirados (msg assinatura)
        for k, exp in list(_DEDUP_MSG_CACHE.items()):  # type: ignore
            if exp < now:
                _DEDUP_MSG_CACHE.pop(k, None)  # type: ignore

        # dedupe por event_id
        if event_id in _DEDUP_EVENT_CACHE:  # type: ignore
            return JSONResponse({"ok": True, "ignored": "duplicate_event", "event_id": event_id})
        _DEDUP_EVENT_CACHE[event_id] = now + ttl_seconds  # type: ignore

        # dedupe por assinatura de mensagem do cliente (telefone+texto)
        msg_sig = f"{telefone}|{(texto or '').strip().lower()}"
        if (telefone and texto) and msg_sig in _DEDUP_MSG_CACHE:  # type: ignore
            return JSONResponse({"ok": True, "ignored": "duplicate_message", "event_id": event_id, "telefone": telefone})
        if telefone and texto:
            _DEDUP_MSG_CACHE[msg_sig] = now + ttl_seconds  # type: ignore

        # IGNORA eventos sem texto (acks/status) para não acionar o orquestrador
        if not texto:
            try:
                sample = {
                    "top_keys": list(p.keys()),
                    "msg_keys": list((p.get("message") or {}).keys()),
                    "fields": {
                        "text": p.get("text"),
                        "body": p.get("body"),
                        "mensagem": p.get("mensagem"),
                        "msg": p.get("msg"),
                        "message.text": (p.get("message") or {}).get("text"),
                        "message.conversation": (p.get("message") or {}).get("conversation"),
                        "message.extendedTextMessage.text": ((p.get("message") or {}).get("extendedTextMessage") or {}).get("text"),
                        "textMessage.text": (p.get("textMessage") or {}).get("text"),
                        "textMessageData.textMessage": (p.get("textMessageData") or {}).get("textMessage"),
                    },
                }
                logger.info(f"[Evolution] empty_text debug event_id={event_id} telefone={telefone} sample={json.dumps(sample, ensure_ascii=False)[:400]}")
            except Exception:
                pass
            logger.info(f"[Evolution] inbound ignorado: empty_text telefone={telefone} event_id={event_id}")
            return JSONResponse({"ok": True, "ignored": "empty_text", "event_id": event_id})

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

        # NEW: repassa event_id para rastreio
        result["event_id"] = event_id

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

            # Envio Evolution com dedupe de saída seguro
            telefone_out = (result.get("cliente") or {}).get("telefone") or telefone
            texto_out = result.get("resposta_bot")

            # Inicializa/prune cache de saídas (sem criar variável local)
            global _SENT_CACHE
            now2 = time.time()
            for k, exp in list(_SENT_CACHE.items()):
                if exp < now2:
                    _SENT_CACHE.pop(k, None)

            send_sig = f"{telefone_out}|{(texto_out or '').strip().lower()}"
            if telefone_out and texto_out:
                if send_sig in _SENT_CACHE:
                    result["enviado_via_evolution"] = False
                    result["evolution_status"] = {"skipped": "duplicate_outgoing", "send_sig": send_sig}
                else:
                    evo = await send_text(telefone_out, texto_out)
                    result["enviado_via_evolution"] = bool(evo.get("sent"))
                    result["evolution_status"] = evo
                    _SENT_CACHE[send_sig] = time.time() + ttl_seconds

                    # Enviar snippet do catálogo quando houver ação especial
                    if (result.get("acao_especial") or "").strip() == "[ACAO:ENVIAR_CATALOGO]":
                        try:
                            ctx = build_context_for_intent("Catálogo")
                            prev = (ctx.get("catalog_preview") or "").strip()
                            if prev:
                                lines = [l for l in prev.splitlines() if l.strip()]
                                snippet = "\n".join(lines[:12])
                                await send_text(telefone_out, snippet)
                        except Exception:
                            pass
            # Persistência Supabase
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

@app.post("/whatsapp/webhook")
async def whatsapp_webhook(req: Request):
    try:
        try:
            raw = await req.body()
            logger.debug(f"[WhatsApp] Raw payload recebido: {raw.decode('utf-8', errors='ignore')}")
            try:
                payload = json.loads(raw.decode("utf-8", errors="ignore"))
                # Identifica tipo de evento para debug
                if isinstance(payload, dict) and payload.get("event"):
                    logger.info(f"[WhatsApp] Tipo de evento recebido: {payload['event']}")
            except Exception as e:
                logger.error(f"[WhatsApp] Erro ao decodificar JSON: {str(e)}")
                payload = {}
        except Exception as e:
            logger.error(f"[WhatsApp] Erro ao ler body: {str(e)}")
            payload = {}

        logger.debug(f"[WhatsApp] Payload recebido: {json.dumps(payload, ensure_ascii=False)}")
        try:
            events = parse_incoming_events(payload or {})
            logger.debug(f"[WhatsApp] Tentativa de extração de eventos concluída")
            if not events:
                logger.warning("[WhatsApp] Nenhum evento extraído do payload")
                return JSONResponse({"ok": False, "error": "no_events_extracted"})
            logger.debug(f"[WhatsApp] Eventos extraídos com sucesso: {json.dumps(events, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"[WhatsApp] Erro ao extrair eventos do payload: {str(e)}", exc_info=True)
            return JSONResponse({"ok": False, "error": "event_extraction_failed", "detail": str(e)})
        
        # Usa o cache global para deduplicação

        processed = []
        ignored = []
        for ev in events:
            from_me = bool(ev.get("from_me"))
            telefone = (ev.get("telefone") or "").strip()
            texto = (ev.get("texto") or "").strip()
            event_id = (ev.get("event_id") or f"evt-{int(time.time()*1000)}")

            if from_me:
                logger.info(f"[WhatsApp] inbound ignorado: from_me telefone={telefone} event_id={event_id}")
                ignored.append({"ignored": "from_me", "event_id": event_id, "telefone": telefone})
                continue
            if not texto:
                logger.info(f"[WhatsApp] inbound ignorado: empty_text telefone={telefone} event_id={event_id}")
                ignored.append({"ignored": "empty_text", "event_id": event_id, "telefone": telefone})
                continue

            # IGNORA eventos sem texto (acks/status)
            if not texto:
                ignored.append({"ignored": "empty_text", "event_id": event_id, "telefone": telefone})
                continue

            # dedupe por event_id e assinatura
            import time
            now = time.time()
            ttl = 180  # 3 minutos de TTL para deduplicação
            if event_id in _DEDUP_EVENT_CACHE:  # type: ignore
                ignored.append({"ignored": "duplicate_event", "event_id": event_id})
                continue
            _DEDUP_EVENT_CACHE[event_id] = now + ttl  # type: ignore

            # Verifica duplicação usando cache global
            if _check_global_dedup(telefone, texto, event_id):
                ignored.append({"ignored": "duplicate_message", "event_id": event_id, "telefone": telefone})
                continue

            logger.info(f"[WhatsApp] inbound: telefone={telefone} len(texto)={len(texto)} event_id={event_id}")

            internal = {
                "acao": "receber-mensagem",
                "mensagem": texto,
                "telefoneCliente": telefone,
                "dryRun": False,
                "source": "whatsapp",  # Identifica origem da mensagem
            }

            try:
                logger.info(f"[WhatsApp] processando mensagem: telefone={telefone} texto={texto}")
                result = await handle_message(internal)
                logger.info(f"[WhatsApp] resposta do orquestrador: {json.dumps(result, ensure_ascii=False)}")
            except Exception as e:
                logger.error(f"Falha no orquestrador (/whatsapp/webhook): {str(e)}", exc_info=True)
                processed.append({"ok": False, "error": "orchestrator_failed", "detail": str(e), "event_id": event_id})
                continue

            if not isinstance(result, dict):
                processed.append({"ok": False, "error": "orchestrator_invalid_response", "event_id": event_id})
                continue

            # normaliza texto de saída e anexa event_id
            rb = result.get("resposta_bot")
            cc = result.get("contexto_conversa")
            if isinstance(rb, str) and rb:
                result["resposta_bot"] = _normalize_ptbr(rb)
            if isinstance(cc, str) and cc:
                result["contexto_conversa"] = _normalize_ptbr(cc)
            result["event_id"] = event_id

            # envio Evolution com dedupe de saída
            try:
                telefone_out = (result.get("cliente") or {}).get("telefone") or telefone
                texto_out = result.get("resposta_bot")

                # prune expirados do cache de saídas
                global _SENT_CACHE
                now = time.time()
                for k, exp in list(_SENT_CACHE.items()):
                    if exp < now:
                        _SENT_CACHE.pop(k, None)

                send_sig = f"{telefone_out}|{(texto_out or '').strip().lower()}"
                if telefone_out and texto_out:
                    if send_sig in _SENT_CACHE:
                        result["enviado_via_evolution"] = False
                        result["evolution_status"] = {"skipped": "duplicate_outgoing", "send_sig": send_sig}
                    else:
                        evo = await send_text(telefone_out, texto_out)
                        result["enviado_via_evolution"] = bool(evo.get("sent"))
                        result["evolution_status"] = evo
                        _SENT_CACHE[send_sig] = now + DEDUPE_TTL_SECONDS

                        # Enviar snippet do catálogo quando houver ação especial
                        if (result.get("acao_especial") or "").strip() == "[ACAO:ENVIAR_CATALOGO]":
                            try:
                                ctx = build_context_for_intent("Catálogo")
                                prev = (ctx.get("catalog_preview") or "").strip()
                                if prev:
                                    lines = [l for l in prev.splitlines() if l.strip()]
                                    snippet = "\n".join(lines[:12])
                                    await send_text(telefone_out, snippet)
                            except Exception:
                                pass

                # Persistência Supabase
                try:
                    supa = await persist_conversation(result)
                    result["persistencia_supabase"] = supa
                except Exception as e:
                    logger.error(f"[WhatsApp] Falha ao enviar/registrar resposta: {str(e)}", exc_info=True)
                    result["enviado_via_evolution"] = False
                    result["evolution_status"] = {"error": str(e)}
                    result["persistencia_supabase"] = {"ok": False, "error": str(e)}
            except Exception as e:
                # fecha o try externo (envio/persistência) e marca erro
                logger.error(f"[WhatsApp] Falha no envio/persistência: {str(e)}", exc_info=True)
                result["enviado_via_evolution"] = False
                result["evolution_status"] = {"error": str(e)}
                if not result.get("persistencia_supabase"):
                    result["persistencia_supabase"] = {"ok": False, "error": str(e)}
            processed.append(_json_safe(result))

        return JSONResponse({"ok": True, "processed": processed, "ignored": ignored}, media_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error("Falha ao processar /whatsapp/webhook", exc_info=True)
        return JSONResponse(_json_safe({"ok": False, "error": "invalid_payload", "detail": str(e)}), media_type="application/json; charset=utf-8")

@app.get("/")
async def root():
    return {
        "ok": True,
        "service": "3A Frios Backend",
        "endpoints": ["/webhook", "/evolution/webhook", "/whatsapp/webhook", "/docs"],
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


# Caches globais e TTL para dedup
DEDUPE_TTL_SECONDS = 180
_GLOBAL_DEDUP_CACHE = {}  # Cache unificado para todas as mensagens
_DEDUP_EVENT_CACHE = {}
_DEDUP_MSG_CACHE = {}
_SENT_CACHE = {}

def _check_global_dedup(telefone: str, texto: str, event_id: str = "") -> bool:
    """Verifica se uma mensagem já foi processada recentemente"""
    try:
        now = time.time()
        # Limpa cache expirado
        for k, (exp, _) in list(_GLOBAL_DEDUP_CACHE.items()):
            if exp < now:
                _GLOBAL_DEDUP_CACHE.pop(k, None)
        
        # Gera assinatura única da mensagem
        msg_sig = f"{telefone}|{texto.lower().strip()}"
        if event_id:
            msg_sig = f"{msg_sig}|{event_id}"
        
        # Verifica se já foi processada
        if msg_sig in _GLOBAL_DEDUP_CACHE:
            return True
        
        # Marca como processada
        _GLOBAL_DEDUP_CACHE[msg_sig] = (now + DEDUPE_TTL_SECONDS, True)
        return False
    except Exception:
        return False