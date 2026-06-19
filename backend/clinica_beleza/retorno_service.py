"""
Retorno gratuito — isenção da taxa de consulta (valor do local de atendimento).

Modos (configuráveis pelo administrador):
- Por procedimento: paciente concluiu procedimento X; dentro de N dias retorna para
  acompanhamento → não paga taxa de consulta (procedimentos cobram normalmente).
- Por consulta: paciente teve qualquer consulta concluída; dentro de N dias → não paga taxa.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Iterable

from django.utils import timezone


@dataclass
class RetornoElegibilidade:
    elegivel: bool
    tipo: str | None = None  # 'procedimento' | 'consulta'
    procedure_id: int | None = None
    procedure_nome: str | None = None
    dias_retorno: int | None = None
    dias_restantes: int | None = None
    consulta_origem_id: int | None = None
    mensagem: str | None = None

    def to_dict(self):
        return {
            'elegivel': self.elegivel,
            'tipo': self.tipo,
            'procedure_id': self.procedure_id,
            'procedure_nome': self.procedure_nome,
            'dias_retorno': self.dias_retorno,
            'dias_restantes': self.dias_restantes,
            'consulta_origem_id': self.consulta_origem_id,
            'mensagem': self.mensagem,
        }


def get_agenda_retorno_config(loja_id):
    from .models import AgendaRetornoConfig

    config, _ = AgendaRetornoConfig.objects.get_or_create(
        loja_id=loja_id,
        defaults={
            'retorno_procedimento_ativo': False,
            'retorno_consulta_ativo': False,
            'dias_retorno_consulta': 30,
        },
    )
    return config


def _aware_dt(dt):
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _data_referencia_consulta(consulta):
    for attr in ('data_fim', 'data_inicio'):
        val = getattr(consulta, attr, None)
        if val:
            return _aware_dt(val)
    appointment = getattr(consulta, 'appointment', None)
    if appointment and getattr(appointment, 'date', None):
        return _aware_dt(appointment.date)
    return None


def _procedure_ids_from_appointment(appointment) -> set[int]:
    ids: set[int] = set()
    if not appointment:
        return ids
    retorno_proc = getattr(appointment, 'retorno_procedure_id', None)
    if retorno_proc:
        ids.add(int(retorno_proc))
    if getattr(appointment, 'procedure_id', None):
        ids.add(int(appointment.procedure_id))
    try:
        for ap in appointment.appointment_procedures.select_related('procedure').all():
            ids.add(int(ap.procedure_id))
    except Exception:
        pass
    return ids


def _procedure_ids_from_consulta(consulta) -> set[int]:
    return _procedure_ids_from_appointment(getattr(consulta, 'appointment', None))


def _consultas_concluidas(patient_id, loja_id, exclude_appointment_id=None):
    from .models import Consulta

    qs = (
        Consulta.objects.filter(
            patient_id=patient_id,
            loja_id=loja_id,
            status='COMPLETED',
        )
        .select_related('appointment')
        .prefetch_related('appointment__appointment_procedures')
        .order_by('-data_fim', '-data_inicio', '-id')
    )
    if exclude_appointment_id:
        qs = qs.exclude(appointment_id=exclude_appointment_id)
    return qs


def _dias_entre(ref, dt):
    ref_local = timezone.localtime(ref)
    dt_local = timezone.localtime(dt)
    return (ref_local.date() - dt_local.date()).days


def verificar_retorno_procedimento(
    patient_id,
    procedure_ids: Iterable[int],
    loja_id,
    *,
    reference_date=None,
    exclude_appointment_id=None,
) -> RetornoElegibilidade | None:
    from .models import RetornoProcedimentoRegra

    config = get_agenda_retorno_config(loja_id)
    if not config.retorno_procedimento_ativo:
        return None

    proc_ids = {int(p) for p in (procedure_ids or []) if p}
    if not proc_ids:
        return None

    regras = list(
        RetornoProcedimentoRegra.objects.filter(
            loja_id=loja_id,
            is_active=True,
            procedure_id__in=proc_ids,
        ).select_related('procedure')
    )
    if not regras:
        return None

    ref = _aware_dt(reference_date) or timezone.now()
    regra_por_proc = {r.procedure_id: r for r in regras}

    for consulta in _consultas_concluidas(patient_id, loja_id, exclude_appointment_id):
        hist_procs = _procedure_ids_from_consulta(consulta)
        dt = _data_referencia_consulta(consulta)
        if not dt:
            continue
        for proc_id in hist_procs & proc_ids:
            regra = regra_por_proc.get(proc_id)
            if not regra:
                continue
            dias_passados = _dias_entre(ref, dt)
            if dias_passados <= regra.dias_retorno:
                restantes = regra.dias_retorno - dias_passados
                return RetornoElegibilidade(
                    elegivel=True,
                    tipo='procedimento',
                    procedure_id=proc_id,
                    procedure_nome=regra.procedure.nome,
                    dias_retorno=regra.dias_retorno,
                    dias_restantes=max(0, restantes),
                    consulta_origem_id=consulta.id,
                    mensagem=(
                        f'Retorno de acompanhamento — {regra.procedure.nome} '
                        f'({restantes} dia(s) restantes no prazo de {regra.dias_retorno}). '
                        f'Taxa de consulta isenta.'
                    ),
                )
    return None


def verificar_retorno_consulta(
    patient_id,
    loja_id,
    *,
    reference_date=None,
    exclude_appointment_id=None,
) -> RetornoElegibilidade | None:
    config = get_agenda_retorno_config(loja_id)
    if not config.retorno_consulta_ativo or config.dias_retorno_consulta <= 0:
        return None

    ref = _aware_dt(reference_date) or timezone.now()
    dias_limite = int(config.dias_retorno_consulta)

    for consulta in _consultas_concluidas(patient_id, loja_id, exclude_appointment_id):
        dt = _data_referencia_consulta(consulta)
        if not dt:
            continue
        dias_passados = _dias_entre(ref, dt)
        if dias_passados <= dias_limite:
            restantes = dias_limite - dias_passados
            return RetornoElegibilidade(
                elegivel=True,
                tipo='consulta',
                dias_retorno=dias_limite,
                dias_restantes=max(0, restantes),
                consulta_origem_id=consulta.id,
                mensagem=(
                    f'Retorno por consulta ({restantes} dia(s) restantes no prazo de {dias_limite}). '
                    f'Taxa de consulta isenta.'
                ),
            )
    return None


def verificar_retorno(
    patient_id,
    procedure_ids,
    loja_id,
    *,
    reference_date=None,
    exclude_appointment_id=None,
) -> RetornoElegibilidade:
    """Verifica retorno por procedimento (prioridade) e depois por consulta."""
    proc = verificar_retorno_procedimento(
        patient_id,
        procedure_ids,
        loja_id,
        reference_date=reference_date,
        exclude_appointment_id=exclude_appointment_id,
    )
    if proc and proc.elegivel:
        return proc

    cons = verificar_retorno_consulta(
        patient_id,
        loja_id,
        reference_date=reference_date,
        exclude_appointment_id=exclude_appointment_id,
    )
    if cons and cons.elegivel:
        return cons

    return RetornoElegibilidade(elegivel=False)


def verificar_retorno_appointment(appointment, reference_date=None) -> RetornoElegibilidade:
    procedure_ids = _procedure_ids_from_appointment(appointment)
    return verificar_retorno(
        appointment.patient_id,
        procedure_ids,
        appointment.loja_id,
        reference_date=reference_date or getattr(appointment, 'date', None),
        exclude_appointment_id=appointment.id,
    )


def aplicar_retorno_em_consulta(consulta, appointment=None) -> RetornoElegibilidade:
    """Zera valor_consulta quando elegível; persiste flags na consulta."""
    appointment = appointment or consulta.appointment
    resultado = verificar_retorno_appointment(appointment)
    update_fields = ['updated_at']

    if resultado.elegivel:
        if Decimal(str(consulta.valor_consulta or 0)) > 0 or not consulta.retorno_gratuito:
            consulta.valor_consulta = Decimal('0')
            update_fields.append('valor_consulta')
        if not consulta.retorno_gratuito:
            consulta.retorno_gratuito = True
            update_fields.append('retorno_gratuito')
        if consulta.retorno_tipo != (resultado.tipo or ''):
            consulta.retorno_tipo = resultado.tipo or ''
            update_fields.append('retorno_tipo')
        if len(update_fields) > 1:
            consulta.save(update_fields=update_fields)

    return resultado


def valor_consulta_com_retorno(appointment, valor_base: Decimal) -> tuple[Decimal, RetornoElegibilidade]:
    """Retorna (valor_consulta_ajustado, elegibilidade)."""
    resultado = verificar_retorno_appointment(appointment)
    if resultado.elegivel:
        return Decimal('0'), resultado
    return valor_base, resultado
