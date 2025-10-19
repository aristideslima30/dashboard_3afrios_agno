import typing as _t

# Parser unificado de payloads de WhatsApp (Cloud API, WAHA, Evolution)
# Retorna uma lista de eventos normalizados: { telefone: str, texto: str, event_id: str, from_me: bool }

def _digits(s: str | None) -> str:
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _extract_evolution(payload: dict) -> _t.List[dict]:
    events: _t.List[dict] = []
    from_me_keys = ("fromMe",)

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
        return (
            ((p.get("key") or {}).get("id"))
            or p.get("id")
            or ((payload.get("key") or {}).get("id"))
            or payload.get("id")
            or ""
        )

    # Evolution pode vir com messages[] ou campos diretos
    items = []
    if isinstance(payload, dict) and isinstance(payload.get("messages"), list) and payload["messages"]:
        items = [payload["messages"][0] or {}]
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
        # texto
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
        texto = str(t or "").strip()
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
    if not isinstance(payload, dict):
        return []

    events: _t.List[dict] = []
    # Evolution
    ev = _extract_evolution(payload)
    for e in ev:
        txt = str(e.get("texto") or "").strip()
        if e.get("from_me") or (e.get("telefone") and txt):
            events.append(e)
    if events:
        return events

    # Cloud API
    cl = _extract_cloud_api(payload)
    for e in cl:
        txt = str(e.get("texto") or "").strip()
        if e.get("from_me") or (e.get("telefone") and txt):
            events.append(e)
    if events:
        return events

    # WAHA
    wh = _extract_waha(payload)
    for e in wh:
        txt = str(e.get("texto") or "").strip()
        if e.get("from_me") or (e.get("telefone") and txt):
            events.append(e)
    if events:
        return events

    # Heurística genérica
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
        return [{"from_me": False, "telefone": base_phone, "texto": str(texto or "").strip(), "event_id": payload.get("id") or ""}]

    return []