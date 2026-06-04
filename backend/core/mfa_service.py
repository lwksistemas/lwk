"""
MFA TOTP (Google Authenticator, etc.) para usuários do sistema.
"""
from __future__ import annotations

import base64
import io
import logging
from typing import Optional, Tuple

from django.conf import settings

try:
    import pyotp
except ImportError:
    pyotp = None  # type: ignore

from core.encryption import decrypt_value, encrypt_value, is_encrypted

logger = logging.getLogger(__name__)

ISSUER = getattr(settings, 'MFA_TOTP_ISSUER', 'LWK Sistemas')


def _require_pyotp():
    if pyotp is None:
        raise RuntimeError('Dependência pyotp não instalada. Execute: pip install pyotp')


def generate_totp_secret() -> str:
    _require_pyotp()
    return pyotp.random_base32()


def encrypt_totp_secret(secret: str) -> str:
    return encrypt_value(secret.strip())


def decrypt_totp_secret(stored: str) -> str:
    if not stored:
        return ''
    return decrypt_value(stored).strip()


def provisioning_uri(email: str, secret: str) -> str:
    _require_pyotp()
    return pyotp.TOTP(secret).provisioning_uri(name=email or 'usuario', issuer_name=ISSUER)


def verify_totp_code(secret: str, code: str, *, valid_window: int = 1) -> bool:
    if not secret or not code:
        return False
    normalized = ''.join(c for c in str(code).strip() if c.isdigit())
    if len(normalized) != 6:
        return False
    try:
        _require_pyotp()
        totp = pyotp.TOTP(secret)
        return totp.verify(normalized, valid_window=valid_window)
    except Exception as e:
        logger.warning('verify_totp_code: %s', e)
        return False


def qr_code_base64(uri: str) -> str:
    """PNG em base64 para exibir QR no frontend."""
    try:
        import qrcode
    except ImportError:
        logger.warning('qrcode não instalado — retornando sem imagem QR')
        return ''

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')
