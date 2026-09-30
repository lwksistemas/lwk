"""Normalização e validação de chaves API Asaas (legado, prod e sandbox)."""


def normalize_asaas_api_key(key: str) -> str:
    """Corrige cópia sem cifrão ($) — comum ao colar do painel/chat.
    Produção: $aact_prod_{hash} | Sandbox: $aact_hmlg_{hash} | Legado: $aact_{hash}
    """
    key = (key or "").strip()
    if key.startswith("aact_") and not key.startswith("$aact_"):
        key = f"${key}"
    return key


def is_valid_asaas_api_key(key: str) -> bool:
    key = normalize_asaas_api_key(key)
    return (
        key.startswith("$aact_")
        and "..." not in key
        and len(key) >= 40
    )


def criptografar_asaas_api_key(key: str) -> str:
    """Normaliza e grava com o prefixo enc::. Cada app guarda o resultado no próprio campo."""
    from core.encryption import encrypt_value, is_encrypted

    norm = normalize_asaas_api_key(key)
    if not norm or is_encrypted(norm):
        return norm
    return encrypt_value(norm)


def chave_asaas_em_claro(key: str) -> str:
    """Devolve a chave utilizável, venha em texto ou já criptografada."""
    from core.encryption import decrypt_value

    return normalize_asaas_api_key(decrypt_value(key or ""))


def asaas_key_is_sandbox(key: str) -> bool:
    key = normalize_asaas_api_key(key)
    if not key:
        return True
    if "_prod_" in key:
        return False
    if "_hmlg_" in key or "hmlg" in key:
        return True
    return "hmlg" in key
