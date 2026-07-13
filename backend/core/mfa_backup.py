"""Códigos de recuperação MFA (uso único) para superadmin/suporte.
Armazenados como hashes SHA-256 em JSON criptografado (Fernet).
"""
from __future__ import annotations

import hashlib
import json
import logging
import secrets

from core.encryption import decrypt_value, encrypt_value

logger = logging.getLogger(__name__)

BACKUP_CODE_COUNT = 8
# Sem caracteres ambíguos (0/O, 1/I/L)
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _normalize_code(code: str) -> str:
    return "".join(c for c in (code or "").upper() if c.isalnum())


def _hash_code(normalized: str) -> str:
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def generate_backup_codes(count: int = BACKUP_CODE_COUNT) -> list[str]:
    """Gera códigos no formato XXXX-XXXX para exibição única ao usuário."""
    codes = []
    for _ in range(count):
        part1 = "".join(secrets.choice(_ALPHABET) for _ in range(4))
        part2 = "".join(secrets.choice(_ALPHABET) for _ in range(4))
        codes.append(f"{part1}-{part2}")
    return codes


def store_backup_hashes(hashes: list[str]) -> str:
    return encrypt_value(json.dumps(hashes))


def load_backup_hashes(encrypted: str) -> list[str]:
    if not encrypted:
        return []
    try:
        raw = decrypt_value(encrypted)
        data = json.loads(raw) if raw else []
        return [h for h in data if isinstance(h, str) and h]
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning("mfa_backup: falha ao carregar hashes: %s", e)
        return []


def backup_codes_remaining(encrypted: str) -> int:
    return len(load_backup_hashes(encrypted))


def issue_backup_codes(count: int = BACKUP_CODE_COUNT) -> tuple[list[str], str]:
    """Retorna (códigos em texto claro, blob criptografado para salvar)."""
    plain = generate_backup_codes(count)
    hashes = [_hash_code(_normalize_code(c)) for c in plain]
    return plain, store_backup_hashes(hashes)


def verify_and_consume_backup_code(encrypted: str, code: str) -> tuple[bool, str]:
    """Valida código de recuperação e remove o hash usado.
    Retorna (ok, novo_blob_criptografado).
    """
    normalized = _normalize_code(code)
    if len(normalized) < 8:
        return False, encrypted or ""

    hashes = load_backup_hashes(encrypted)
    if not hashes:
        return False, encrypted or ""

    digest = _hash_code(normalized)
    if digest not in hashes:
        return False, encrypted or ""

    hashes = [h for h in hashes if h != digest]
    return True, store_backup_hashes(hashes)
