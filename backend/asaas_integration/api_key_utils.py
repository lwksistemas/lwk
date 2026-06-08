"""Normalização e validação de chaves API Asaas (legado, prod e sandbox)."""


def normalize_asaas_api_key(key: str) -> str:
    """
    Corrige cópia sem cifrão ($) — comum ao colar do painel/chat.
    Produção: $aact_prod_{hash} | Sandbox: $aact_hmlg_{hash} | Legado: $aact_{hash}
    """
    key = (key or '').strip()
    if key.startswith('aact_') and not key.startswith('$aact_'):
        key = f'${key}'
    return key


def is_valid_asaas_api_key(key: str) -> bool:
    key = normalize_asaas_api_key(key)
    return (
        key.startswith('$aact_')
        and '...' not in key
        and len(key) >= 40
    )


def asaas_key_is_sandbox(key: str) -> bool:
    key = normalize_asaas_api_key(key)
    if not key:
        return True
    if '_prod_' in key:
        return False
    if '_hmlg_' in key or 'hmlg' in key:
        return True
    return 'hmlg' in key
