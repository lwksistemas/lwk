"""Utilitários de CEP (cadastro de lojas, NFS-e)."""
import re


def cep_apenas_digitos(valor: str | None) -> str:
    return re.sub(r'\D', '', valor or '')


def cep_digitos_validos(valor: str | None) -> bool:
    return len(cep_apenas_digitos(valor)) == 8


def normalizar_cep(valor: str | None) -> str:
    """
    Formata CEP como XXXXX-XXX.
    Completa com zero à esquerda quando a Receita/BrasilAPI omite (ex.: 1310100 → 01310-100).
    """
    digits = cep_apenas_digitos(valor)
    if not digits:
        return ''
    if len(digits) < 8:
        digits = digits.zfill(8)
    elif len(digits) > 8:
        digits = digits[:8]
    return f'{digits[:5]}-{digits[5:8]}'
