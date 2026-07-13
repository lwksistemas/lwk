"""Módulo de criptografia para campos sensíveis.

Usa Fernet (AES-128-CBC + HMAC-SHA256) do pacote cryptography.
A chave usa FIELD_ENCRYPTION_KEY (recomendado em produção) ou SECRET_KEY via PBKDF2.

Uso:
    from core.encryption import encrypt_value, decrypt_value

    # Criptografar antes de salvar
    config.issnet_senha = encrypt_value('minha_senha_secreta')

    # Descriptografar ao usar
    senha_real = decrypt_value(config.issnet_senha)
"""
import base64
import logging

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Falha ao criptografar — não armazenar plaintext."""

# Cache da instância Fernet (criada uma vez por processo)
_fernet_instance = None

# Prefixo para identificar valores já criptografados
ENCRYPTED_PREFIX = "enc::"


def _encryption_secret_bytes() -> bytes:
    dedicated = (getattr(settings, "FIELD_ENCRYPTION_KEY", None) or "").strip()
    if dedicated:
        return dedicated.encode("utf-8")
    return settings.SECRET_KEY.encode("utf-8")


def _get_fernet() -> Fernet:
    """Retorna instância Fernet (FIELD_ENCRYPTION_KEY ou SECRET_KEY)."""
    global _fernet_instance
    if _fernet_instance is None:
        secret = _encryption_secret_bytes()
        # Derivar chave de 32 bytes via PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"lwk-nfse-encryption-salt-v1",
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret))
        _fernet_instance = Fernet(key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    """Criptografa um valor de texto.
    Retorna string com prefixo 'enc::' + token Fernet base64.
    Se o valor já estiver criptografado, retorna sem alterar.
    Se o valor for vazio, retorna vazio.
    """
    if not plaintext:
        return ""
    if plaintext.startswith(ENCRYPTED_PREFIX):
        return plaintext  # Já criptografado
    try:
        f = _get_fernet()
        token = f.encrypt(plaintext.encode("utf-8"))
        return ENCRYPTED_PREFIX + token.decode("utf-8")
    except Exception as e:
        logger.error("Erro ao criptografar valor: %s", e)
        raise EncryptionError("Falha ao criptografar dado sensível") from e


def decrypt_value(ciphertext: str) -> str:
    """Descriptografa um valor criptografado.
    Se o valor não tiver o prefixo 'enc::', assume que é plaintext (migração gradual).
    Se o valor for vazio, retorna vazio.
    """
    if not ciphertext:
        return ""
    if not ciphertext.startswith(ENCRYPTED_PREFIX):
        return ciphertext  # Plaintext (ainda não migrado)
    try:
        f = _get_fernet()
        token = ciphertext[len(ENCRYPTED_PREFIX):].encode("utf-8")
        return f.decrypt(token).decode("utf-8")
    except InvalidToken:
        logger.error("Token de criptografia inválido — possível corrupção ou troca de SECRET_KEY")
        return ""
    except Exception as e:
        logger.error("Erro ao descriptografar valor: %s", e)
        return ""


def is_encrypted(value: str) -> bool:
    """Verifica se um valor já está criptografado."""
    return bool(value) and value.startswith(ENCRYPTED_PREFIX)
