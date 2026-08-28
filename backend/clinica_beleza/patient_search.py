"""Busca de pacientes por nome, CPF, telefone e e-mail."""

from django.db.models import F, Q, Value
from django.db.models.functions import Coalesce, Replace

_PUNCT_TO_STRIP = (".", "-", "/", "(", ")", " ", "+")


def digits_only(value: str) -> str:
    return "".join(c for c in (value or "") if c.isdigit())


def _digits_expr(field: str):
    expr = Coalesce(F(field), Value(""))
    for ch in _PUNCT_TO_STRIP:
        expr = Replace(expr, Value(ch), Value(""))
    return expr


def apply_patient_search(queryset, search: str):
    """Filtra pacientes: nome por trecho; CPF/telefone ignorando pontuação."""
    search = (search or "").strip()
    if not search:
        return queryset

    digits = digits_only(search)
    qs = queryset.annotate(
        _cpf_digits=_digits_expr("cpf"),
        _tel_digits=_digits_expr("telefone"),
    )

    if "@" in search:
        return qs.filter(Q(email__icontains=search))

    q = Q(nome__icontains=search)
    if len(digits) >= 3:
        q |= Q(_cpf_digits__icontains=digits) | Q(_tel_digits__icontains=digits)
        q |= Q(cpf__icontains=search) | Q(telefone__icontains=search)
    if len(search) >= 3:
        q |= Q(email__icontains=search)
    return qs.filter(q)
