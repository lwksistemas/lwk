"""Regras da agenda do salão: intervalo, conflito e leitura de data."""
from datetime import datetime, timedelta

from django.db.models import Q
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


def avaliar_jornada(entrada, saida, intervalo_inicio, intervalo_fim, inicio, fim) -> str | None:
    """Recusa atendimento fora do expediente ou em cima do intervalo."""
    if inicio >= fim:
        return "O horário de saída precisa ser depois da entrada."
    if inicio < entrada or fim > saida:
        return "Este horário está fora da jornada do profissional."
    if intervalo_inicio and intervalo_fim and inicio < intervalo_fim and intervalo_inicio < fim:
        return "Este horário cai no intervalo do profissional."
    return None


def conflito_horario(profissional_id: int, inicio, fim, ignorar_id=None) -> str | None:
    """Devolve a mensagem se o profissional já tem horário, folga ou bloqueio nesse intervalo."""
    mensagem_jornada = _fora_da_jornada(profissional_id, inicio, fim)
    if mensagem_jornada:
        return mensagem_jornada
    from .procedimentos_service import linhas_do_agendamento, montar_fatias

    candidatos = Agendamento.objects.filter(
        status__in=STATUS_OCUPA_HORARIO,
        inicio__lt=fim,
        inicio__gte=inicio - timedelta(hours=12),
    ).filter(
        Q(profissional_id=profissional_id) | Q(procedimentos__profissional_id=profissional_id)
    ).distinct().prefetch_related("procedimentos__servico", "procedimentos__profissional")
    if ignorar_id:
        candidatos = candidatos.exclude(pk=ignorar_id)
    for outro in candidatos:
        for fatia in montar_fatias(outro.inicio, linhas_do_agendamento(outro))[0]:
            if getattr(fatia["profissional"], "id", None) != int(profissional_id):
                continue
            if intervalos_conflitam(inicio, fim, fatia["inicio"], fatia["fim"]):
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


def _fora_da_jornada(profissional_id: int, inicio, fim) -> str | None:
    from .models import HorarioTrabalho

    local_inicio = timezone.localtime(inicio)
    local_fim = timezone.localtime(fim)
    if local_inicio.date() != local_fim.date():
        return "O atendimento precisa caber no mesmo dia."
    horarios = list(HorarioTrabalho.objects.filter(profissional_id=profissional_id))
    if not horarios:
        return None
    do_dia = next((item for item in horarios if item.dia_semana == local_inicio.weekday() and item.ativo), None)
    if do_dia is None:
        return "Este profissional não atende neste dia."
    return avaliar_jornada(
        do_dia.hora_entrada,
        do_dia.hora_saida,
        do_dia.intervalo_inicio,
        do_dia.intervalo_fim,
        local_inicio.time().replace(microsecond=0),
        local_fim.time().replace(microsecond=0),
    )


def models_profissional(profissional_id: int):
    from django.db.models import Q

    return Q(profissional_id=profissional_id) | Q(profissional__isnull=True)
