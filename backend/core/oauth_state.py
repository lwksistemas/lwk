"""State assinado para fluxos OAuth (Google Calendar, etc.)."""
from __future__ import annotations

from typing import Optional, Tuple

from django.core import signing

OAUTH_STATE_SALT = 'lwk-oauth-state-v1'
OAUTH_STATE_MAX_AGE = 3600  # 1 hora


def encode_oauth_state(loja_id: int, vendedor_id: Optional[int] = None) -> str:
    payload = {'loja_id': int(loja_id)}
    if vendedor_id is not None:
        payload['vendedor_id'] = int(vendedor_id)
    return signing.dumps(payload, salt=OAUTH_STATE_SALT)


def parse_oauth_state(state: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Retorna (loja_id, vendedor_id).
    Aceita state assinado (atual) ou legado 'loja_id' / 'loja_id:vendedor_id'.
    """
    if not state:
        return None, None

    raw = str(state).strip()
    try:
        data = signing.loads(raw, salt=OAUTH_STATE_SALT, max_age=OAUTH_STATE_MAX_AGE)
        if isinstance(data, dict) and data.get('loja_id'):
            loja_id = int(data['loja_id'])
            vendedor_id = data.get('vendedor_id')
            return loja_id, int(vendedor_id) if vendedor_id is not None else None
    except signing.BadSignature:
        pass

    parts = raw.split(':')
    try:
        loja_id = int(parts[0])
        vendedor_id = int(parts[1]) if len(parts) > 1 and parts[1] else None
        return loja_id, vendedor_id
    except (ValueError, TypeError):
        return None, None
