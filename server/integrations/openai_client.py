from openai import OpenAI
from ..config import OPENAI_ENABLED, OPENAI_API_KEY, OPENAI_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def generate_response(system_prompt: str, user_message: str) -> str:
    if not OPENAI_ENABLED or not _client:
        return ""
    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content or ""

def polish_text_ptbr(text: str) -> str:
    # Usa o modelo para revisar ortografia/pontuação sem alterar o sentido
    if not OPENAI_ENABLED or not _client:
        return text
    system = (
        "Você é um revisor de texto em português (pt-BR). "
        "Corrija acentuação, ortografia, pontuação e espaçamento, "
        "mantendo o sentido e sem mudar nomes/valores. Não use emojis."
    )
    resp = _client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        temperature=0.0,
    )
    return (resp.choices[0].message.content or text).strip()