"""Utilitários para conversão segura de valores em Decimal."""
from decimal import Decimal, InvalidOperation


def to_decimal(value, field_name='valor'):
    """Converte value em Decimal ou retorna None se vazio/nulo.

    Levanta ValueError com mensagem descritiva quando o valor é inválido.
    """
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} inválido.') from exc
