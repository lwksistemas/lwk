"""Helpers para bloqueios de horário (data + hora separados no model)."""
from datetime import datetime, time

from django.utils import timezone


def _aware(dt: datetime) -> datetime:
    if timezone.is_aware(dt):
        return dt
    return timezone.make_aware(dt, timezone.get_current_timezone())


def bloqueio_datetime_range(bloqueio) -> tuple[datetime, datetime]:
    """
    Converte BloqueioHorario (data_inicio/fim + horario_inicio/fim) em intervalo datetime.
    Sem horário = dia inteiro.
    """
    start_date = bloqueio.data_inicio
    end_date = bloqueio.data_fim or bloqueio.data_inicio

    if getattr(bloqueio, 'horario_inicio', None):
        start = datetime.combine(start_date, bloqueio.horario_inicio)
    else:
        start = datetime.combine(start_date, time.min)

    if getattr(bloqueio, 'horario_fim', None):
        end = datetime.combine(end_date, bloqueio.horario_fim)
    else:
        end = datetime.combine(end_date, time.max.replace(microsecond=0))

    return _aware(start), _aware(end)


def split_datetime_range(start: datetime, end: datetime, *, dia_inteiro: bool = False) -> dict:
    """Separa datetimes para campos do model BloqueioHorario.

    Se dia_inteiro=True, grava só as datas (horario_inicio/fim = None = dia todo).
    """
    if timezone.is_aware(start):
        start = timezone.localtime(start)
    if timezone.is_aware(end):
        end = timezone.localtime(end)
    if dia_inteiro:
        return {
            'data_inicio': start.date(),
            'data_fim': end.date(),
            'horario_inicio': None,
            'horario_fim': None,
        }
    return {
        'data_inicio': start.date(),
        'data_fim': end.date(),
        'horario_inicio': start.time().replace(microsecond=0),
        'horario_fim': end.time().replace(microsecond=0),
    }


def intervalos_sobrepoem(inicio_a, fim_a, inicio_b, fim_b) -> bool:
    return inicio_a < fim_b and fim_a > inicio_b
