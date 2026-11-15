"""Regras da agenda do salão: intervalo, conflito e leitura de data."""
from datetime import datetime, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import STATUS_OCUPA_HORARIO, Agendamento, Bloqueio


def intervalos_conflitam(inicio_a, fim_a, inicio_b, fim_b) -> bool:
    return inicio_a < fim_b and inicio_b < fim_a


def interpretar_inicio(valor: str):
    texto = (valor or "").strip()
    dt = parse_datetime(texto)
    if dt is None and len(texto) >= 16:
        dt = datetime.strptime(texto[:16], "%Y-%m-%dT%H:%M")
    if dt is None:
        raise ValueError("Informe data e hora do agendamento.")
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _bloqueio_ocupa(bloqueio: Bloqueio, inicio, fim) -> bool:
    dia = timezone.localtime(inicio).date()
    if dia < bloqueio.data_inicio or dia > bloqueio.data_fim:
        return False
    if not bloqueio.horario_inicio or not bloqueio.horario_fim:
        return True
    tz = timezone.get_current_timezone()
    b_ini = timezone.make_aware(datetime.combine(dia, bloqueio.horario_inicio), tz)
    b_fim = timezone.make_aware(datetime.combine(dia, bloqueio.horario_fim), tz)
    return intervalos_conflitam(inicio, fim, b_ini, b_fim)


def conflito_horario(profissional_id: int, inicio, fim, ignorar_id=None) -> str | None:
    """Devolve a mensagem se o profissional já tem horário ou bloqueio nesse intervalo."""
    qs = Agendamento.objects.filter(
        profissional_id=profissional_id,
        status__in=STATUS_OCUPA_HORARIO,
        inicio__lt=fim,
        inicio__gte=inicio - timedelta(hours=12),
    )
    if ignorar_id:
        qs = qs.exclude(pk=ignorar_id)
    for outro in qs:
        if intervalos_conflitam(inicio, fim, outro.inicio, outro.fim):
            return "Este horário já está ocupado para este profissional."
    bloqueios = Bloqueio.objects.filter(
        is_active=True,
        data_inicio__lte=timezone.localtime(fim).date(),
        data_fim__gte=timezone.localtime(inicio).date(),
    ).filter(models_profissional(profissional_id))
    for bloqueio in bloqueios:
        if _bloqueio_ocupa(bloqueio, inicio, fim):
            return "Este horário está bloqueado na agenda."
    return None


def models_profissional(profissional_id: int):
    from django.db.models import Q

    return Q(profissional_id=profissional_id) | Q(profissional__isnull=True)
