"""Sanitização de termos de busca para queries no Postgres.

Postgres rejeita o byte nulo (\\x00) em literais de texto; sem limpeza a
busca autenticada vira 500 em vez de resultado vazio/filtrado.
"""


def sanitize_search_term(value: str | None) -> str:
    """Remove NULs e espaços nas pontas do termo de busca."""
    return (value or "").replace("\x00", "").strip()
