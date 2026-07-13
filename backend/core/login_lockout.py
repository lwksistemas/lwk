"""Bloqueio temporário de conta após tentativas falhas de login (por username).
Persistido no banco default — funciona com múltiplos workers Gunicorn.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

DEFAULT_MAX_FAILURES = 5
DEFAULT_LOCKOUT_MINUTES = 15


def _max_failures() -> int:
    return int(getattr(settings, "LOGIN_MAX_FAILURES", DEFAULT_MAX_FAILURES))


def _lockout_minutes() -> int:
    return int(getattr(settings, "LOGIN_LOCKOUT_MINUTES", DEFAULT_LOCKOUT_MINUTES))


def normalize_username(username: str) -> str:
    return (username or "").strip().lower()[:150]


def check_account_locked(username: str):
    """Retorna datetime de desbloqueio se ainda bloqueado, ou None.
    """
    from superadmin.models import LoginLockout

    key = normalize_username(username)
    if not key:
        return None

    row = LoginLockout.objects.filter(username_key=key).first()
    if not row or not row.locked_until:
        return None

    now = timezone.now()
    if row.locked_until > now:
        return row.locked_until

    row.delete()
    return None


def record_login_failure(username: str) -> bool:
    """Registra falha. Retorna True se a conta acabou de ser bloqueada.
    """
    from superadmin.models import LoginLockout

    key = normalize_username(username)
    if not key:
        return False

    max_failures = _max_failures()
    minutes = _lockout_minutes()
    now = timezone.now()

    row, _ = LoginLockout.objects.get_or_create(
        username_key=key,
        defaults={"failed_attempts": 0},
    )
    row.failed_attempts += 1
    row.updated_at = now

    if row.failed_attempts >= max_failures:
        row.locked_until = now + timedelta(minutes=minutes)
        row.save(update_fields=["failed_attempts", "locked_until", "updated_at"])
        logger.warning(
            "login.lockout user_key=%s failures=%s until=%s",
            key, row.failed_attempts, row.locked_until.isoformat(),
        )
        return True

    row.locked_until = None
    row.save(update_fields=["failed_attempts", "locked_until", "updated_at"])
    return False


def clear_login_failures(username: str) -> None:
    from superadmin.models import LoginLockout

    key = normalize_username(username)
    if key:
        LoginLockout.objects.filter(username_key=key).delete()
