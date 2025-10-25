import typing as _t
import json
import logging

logger = logging.getLogger("3afrios.backend")

# Parser unificado de payloads de WhatsApp (Cloud API, WAHA, Evolution)
# Retorna uma lista de eventos normalizados: { telefone: str, texto: str, event_id: str, from_me: bool }

def _digits(s: str | None) -> str:
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _extract_evolution(payload: dict) -> _t.List[dict]:
    events: _t.List[dict] = []
    logger = logging.getLogger("3afrios.backend")

    def is_from_me(p: dict) -> bool:
        try:
            k = p.get("key") or {}
            msg = p.get("message") or {}
            return bool(
                p.get("fromMe") or k.get("fromMe") or msg.get("fromMe")
            )
        except Exception:
            return False

    def get_event_id(p: dict) -> str:
        # Usa timestamp como fallback para garantir um ID único
        import time
        return (
            ((p.get("key") or {}).get("id"))
            or p.get("id")
            or ((payload.get("key") or {}).get("id"))
            or payload.get("id")
            or f"evt-{int(time.time() * 1000)}"
        )

    # Evolution pode vir com messages[] ou data{} ou campos diretos
    items = []
    if isinstance(payload, dict):
        if isinstance(payload.get("messages"), list) and payload["messages"]:
            items = [payload["messages"][0] or {}]
        elif isinstance(payload.get("data"), dict) and payload.get("event") == "messages.upsert":
            logger.debug("[WebhookParser] Evolution: encontrado formato messages.upsert")
            items = [payload["data"]]
        elif isinstance(payload.get("data"), list) and payload.get("event") == "contacts.update":
            # NOVO: Tenta extrair dados de contacts.update quando pode conter mensagem
            logger.debug("[WebhookParser] Evolution: tentando extrair de contacts.update")
            data_array = payload.get("data", [])
            sender = payload.get("sender", "")
            for contact_data in data_array:
                remote_jid = contact_data.get("remoteJid", "")
                if remote_jid and remote_jid != sender:
                    # Cria um item fake com os dados disponíveis
                    fake_item = {
                        "key": {"remoteJid": remote_jid},
                        "fromMe": False,
                        # Tenta pegar texto de algum lugar (improvável mas vamos tentar)
                        "text": "Olá",  # Texto padrão já que contacts.update não tem texto
                        "message": {"conversation": "Olá"}  # Fallback
                    }
                    items = [fake_item]
                    logger.info(f"[WebhookParser] Evolution: criado item fake para {remote_jid}")
                    break
        else:
            items = [payload]

    for p in items:
        if is_from_me(p):
            events.append({"from_me": True, "telefone": "", "texto": "", "event_id": get_event_id(p)})
            continue
        # telefone
        base = p.get("number") or p.get("from") or p.get("telefone") or p.get("phone") or ""
        if not base:
            key = p.get("key") or {}
            remote = key.get("remoteJid") or p.get("chatId") or p.get("sender") or ""
            if isinstance(remote, str) and "@" in remote:
                remote = remote.split("@", 1)[0]
            base = remote or ""
        telefone = _digits(base)
        # texto (apenas strings válidas; evita usar dict diretamente)
        texto = ""
        for cand in [
            p.get("text"),
            p.get("body"),
            p.get("mensagem"),
            p.get("msg"),
        ]:
            if isinstance(cand, str) and cand.strip():
                texto = cand.strip()
                break

        if not texto:
            msg = p.get("message")
            if isinstance(msg, dict):
                for cand in [
                    msg.get("text"),
                    msg.get("conversation"),
                    (msg.get("extendedTextMessage") or {}).get("text"),
                    (msg.get("textMessage") or {}).get("text"),
                    (msg.get("textMessageData") or {}).get("textMessage"),
                    (msg.get("ephemeralMessage") or {}).get("message", {}).get("extendedTextMessage", {}).get("text"),
                    (msg.get("listResponseMessage") or {}).get("title"),
                ]:
                    if isinstance(cand, str) and cand.strip():
                        texto = cand.strip()
                        logger.debug(f"[WebhookParser] Evolution: texto encontrado no campo {cand}")
                        break

        if not texto:
            tm = p.get("textMessage")
            if isinstance(tm, dict):
                for cand in [
                    tm.get("text"),
                    tm.get("textMessage"),
                ]:
                    if isinstance(cand, str) and cand.strip():
                        texto = cand.strip()
                        break

        events.append({"from_me": False, "telefone": telefone, "texto": texto, "event_id": get_event_id(p)})
    return events


def _extract_cloud_api(payload: dict) -> _t.List[dict]:
    # Meta WhatsApp Cloud API: entry[].changes[].value.messages[]
    events: _t.List[dict] = []
    try:
        entries = payload.get("entry") or []
        for e in entries:
            changes = (e or {}).get("changes") or []
            for ch in changes:
                val = (ch or {}).get("value") or {}
                msgs = val.get("messages") or []
                for m in msgs:
                    # ignorar tipos não-texto se necessário, mas extrair fallback
                    tipo = m.get("type")
                    from_me = False  # Cloud API não reenvia mensagens "from me" como inbound
                    phone = _digits(m.get("from") or (val.get("contacts") or [{}])[0].get("wa_id") or "")
                    texto = ""
                    if tipo == "text":
                        texto = str(((m.get("text") or {}).get("body") or "")).strip()
                    elif tipo == "button":
                        texto = str(((m.get("button") or {}).get("text") or "")).strip()
                    elif tipo == "interactive":
                        inter = m.get("interactive") or {}
                        texto = (
                            (inter.get("button_reply") or {}).get("title")
                            or (inter.get("list_reply") or {}).get("title")
                            or ""
                        )
                    else:
                        # fallback para qualquer campo de texto
                        texto = str(
                            ((m.get("text") or {}).get("body")
                             or m.get("body")
                             or "")
                        ).strip()
                    event_id = m.get("id") or ""
                    events.append({"from_me": from_me, "telefone": phone, "texto": texto, "event_id": event_id})
    except Exception:
        pass
    return events


def _extract_waha(payload: dict) -> _t.List[dict]:
    # WAHA formatos comuns: senderData + messageData; ou messages[]
    events: _t.List[dict] = []
    try:
        # Formato com senderData/messageData
        if isinstance(payload.get("senderData"), dict) and isinstance(payload.get("messageData"), dict):
            sd = payload.get("senderData") or {}
            md = payload.get("messageData") or {}
            phone = _digits(sd.get("sender") or (sd.get("chatId") or "").split("@", 1)[0])
            texto = (
                ((md.get("textMessageData") or {}).get("textMessage"))
                or ((md.get("extendedTextMessage") or {}).get("text"))
                or (md.get("text") or "")
            )
            event_id = payload.get("id") or (md.get("id") if isinstance(md.get("id"), str) else "")
            events.append({"from_me": bool(md.get("fromMe")), "telefone": phone, "texto": str(texto or "").strip(), "event_id": event_id})
        # Formato com messages[]
        msgs = payload.get("messages") or []
        for m in msgs:
            phone = _digits((m.get("chatId") or "").split("@", 1)[0] or m.get("sender") or "")
            texto = str(m.get("text") or m.get("body") or "").strip()
            events.append({"from_me": bool(m.get("fromMe")), "telefone": phone, "texto": texto, "event_id": m.get("id") or ""})
    except Exception:
        pass
    return events


def parse_incoming_events(payload: dict) -> _t.List[dict]:
    """
    Tenta extrair eventos de diferentes provedores.
    Ordem: Evolution -> Cloud API -> WAHA. Se nenhum casar, tenta heurísticas genéricas.
    """
    logger.debug("[WebhookParser] Iniciando extração de eventos")
    if not isinstance(payload, dict):
        logger.warning("[WebhookParser] Payload inválido: não é um dicionário")
        return []
    
    # Skip status update events that don't need message extraction
    if isinstance(payload, dict):
        event_type = payload.get("event", "")
        logger.info(f"[WebhookParser] EVENTO RECEBIDO: {event_type}")
        logger.info(f"[WebhookParser] PAYLOAD COMPLETO: {json.dumps(payload, ensure_ascii=False)}")
        
        # NOVA LÓGICA: Se é contacts.update mas tem remoteJid diferente do sender, pode ser mensagem!
        if event_type == "contacts.update":
            data_array = payload.get("data", [])
            sender = payload.get("sender", "")
            if data_array:
                remote_jid = data_array[0].get("remoteJid", "")
                # Se remoteJid é diferente do sender, pode ser uma mensagem recebida
                if remote_jid and remote_jid != sender:
                    logger.info(f"[WebhookParser] POSSÍVEL MENSAGEM DETECTADA em contacts.update: {remote_jid} != {sender}")
                    # Continua processamento em vez de ignorar
                else:
                    logger.debug(f"[WebhookParser] Ignorando evento de status: {event_type}")
                    return []
            else:
                logger.debug(f"[WebhookParser] Ignorando evento de status: {event_type}")
                return []
        
        # TEMPORARIAMENTE COMENTADO PARA DEBUG
        # Ignora apenas eventos que NÃO contêm mensagens
        # if event_type in {"chats.update", "contacts.update", "send.message"}:
        #     logger.debug(f"[WebhookParser] Ignorando evento de status: {event_type}")
        #     return []
        # Processa explicitamente eventos de mensagens
        if event_type in {"messages.upsert", "messages.update"}:
            logger.info(f"[WebhookParser] Processando evento de mensagem: {event_type}")
            # Continua o processamento normal para eventos de mensagens

    events: _t.List[dict] = []
    # Evolution
    logger.debug("[WebhookParser] Tentando extração formato Evolution")
    ev = _extract_evolution(payload)
    logger.debug(f"[WebhookParser] Evolution: {len(ev)} eventos brutos extraídos")
    for e in ev:
        txt = str(e.get("texto") or "").strip()
        if e.get("from_me") or (e.get("telefone") and txt):
            events.append(e)
            logger.debug(f"[WebhookParser] Evolution: evento válido extraído - id={e.get('event_id')} telefone={e.get('telefone')} len_texto={len(txt)}")
    if events:
        logger.info(f"[WebhookParser] Sucesso no formato Evolution: {len(events)} eventos válidos")
        return events

    # Cloud API
    logger.debug("[WebhookParser] Tentando extração formato Cloud API")
    cl = _extract_cloud_api(payload)
    logger.debug(f"[WebhookParser] Cloud API: {len(cl)} eventos brutos extraídos")
    for e in cl:
        txt = str(e.get("texto") or "").strip()
        if e.get("from_me") or (e.get("telefone") and txt):
            events.append(e)
            logger.debug(f"[WebhookParser] Cloud API: evento válido extraído - id={e.get('event_id')} telefone={e.get('telefone')} len_texto={len(txt)}")
    if events:
        logger.info(f"[WebhookParser] Sucesso no formato Cloud API: {len(events)} eventos válidos")
        return events

    # WAHA
    logger.debug("[WebhookParser] Tentando extração formato WAHA")
    wh = _extract_waha(payload)
    logger.debug(f"[WebhookParser] WAHA: {len(wh)} eventos brutos extraídos")
    for e in wh:
        txt = str(e.get("texto") or "").strip()
        if e.get("from_me") or (e.get("telefone") and txt):
            events.append(e)
            logger.debug(f"[WebhookParser] WAHA: evento válido extraído - id={e.get('event_id')} telefone={e.get('telefone')} len_texto={len(txt)}")
    if events:
        logger.info(f"[WebhookParser] Sucesso no formato WAHA: {len(events)} eventos válidos")
        return events

    # Heurística genérica
    logger.debug("[WebhookParser] Tentando extração via heurística genérica")
    base_phone = _digits(
        payload.get("from") or payload.get("number") or payload.get("sender") or (payload.get("chatId") or "").split("@", 1)[0]
    )
    texto = (
        payload.get("text")
        or (payload.get("message") or {}).get("conversation")
        or payload.get("body")
        or payload.get("mensagem")
        or ""
    )
    if base_phone and str(texto or "").strip():
        logger.info(f"[WebhookParser] Sucesso via heurística genérica: telefone={base_phone} len_texto={len(str(texto or '').strip())}")
        return [{"from_me": False, "telefone": base_phone, "texto": str(texto or "").strip(), "event_id": payload.get("id") or ""}]

    logger.warning("[WebhookParser] Nenhum evento extraído após tentar todos os formatos")
    return []