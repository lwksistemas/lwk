"""State assinado para fluxos OAuth (Google Calendar, etc.)."""
from __future__ import annotations

from django.core import signing

OAUTH_STATE_SALT = "lwk-oauth-state-v1"
OAUTH_STATE_MAX_AGE = 3600  # 1 hora


def encode_oauth_state(loja_id: int, vendedor_id: int | None = None) -> str:
    payload = {"loja_id": int(loja_id)}
    if vendedor_id is not None:
        payload["vendedor_id"] = int(vendedor_id)
    return signing.dumps(payload, salt=OAUTH_STATE_SALT)


def parse_oauth_state(state: str | None) -> tuple[int | None, int | None]:
    """Retorna (loja_id, vendedor_id). Só aceita state assinado e dentro do prazo."""
    if not state:
        return None, None

    raw = str(state).strip()
    try:
        data = signing.loads(raw, salt=OAUTH_STATE_SALT, max_age=OAUTH_STATE_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return None, None
    if not isinstance(data, dict) or not data.get("loja_id"):
        return None, None
    try:
        loja_id = int(data["loja_id"])
        vendedor_id = data.get("vendedor_id")
        return loja_id, int(vendedor_id) if vendedor_id is not None else None
    except (TypeError, ValueError):
        return None, None
