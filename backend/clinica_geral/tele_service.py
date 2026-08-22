"""Cota e sala de telemedicina do consultório."""
from __future__ import annotations

from django.db.models import Sum

from .models import Consulta

TETO_PADRAO = 600


class CotaTeleEsgotada(Exception):
    """A cota mensal de telemedicina acabou."""


def url_sala_jitsi(loja_id: int, consulta_id: int) -> str:
    return f"https://meet.jit.si/lwk-cg-{loja_id}-{consulta_id}"


def minutos_validos(raw) -> int:
    try:
        return max(0, int(raw or 0))
    except (TypeError, ValueError):
        return 0


def minutos_usados_no_mes(ano: int, mes: int) -> int:
    return (
        Consulta.objects.filter(data__year=ano, data__month=mes).aggregate(t=Sum("tele_minutos")).get("t") or 0
    )


def abrir_sala(consulta: Consulta, teto: int | None) -> tuple[Consulta, int, int]:
    usados = minutos_usados_no_mes(consulta.data.year, consulta.data.month)
    limite = teto or TETO_PADRAO
    if usados >= limite:
        raise CotaTeleEsgotada("Cota de telemedicina do mês esgotada (10h).")
    if not consulta.tele_sala_url:
        consulta.tele_sala_url = url_sala_jitsi(consulta.loja_id, consulta.id)
        consulta.save(update_fields=["tele_sala_url", "updated_at"])
    return consulta, int(usados), limite


def registrar_minutos(consulta: Consulta, raw_minutos) -> Consulta:
    extra = minutos_validos(raw_minutos)
    consulta.tele_minutos = (consulta.tele_minutos or 0) + extra
    consulta.save(update_fields=["tele_minutos", "updated_at"])
    return consulta
