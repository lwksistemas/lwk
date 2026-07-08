"""Adicionar/remover procedimentos durante consulta em atendimento."""
from __future__ import annotations

from django.db.models import Max

from .convenio_service import resolver_convenio, resolver_preco_procedimento
from .consentimento_service import garantir_termos_procedimento
from .consulta_service.payment import _reabrir_recebimento_apos_procedimento
from .models import AppointmentProcedure, Consulta, ConsultaTermoProcedimento, Procedure


def _resolver_convenio_consulta(consulta) -> object | None:
    appointment = consulta.appointment
    convenio = getattr(appointment, 'convenio', None) or getattr(consulta, 'convenio', None)
    if convenio:
        return convenio
    patient = getattr(appointment, 'patient', None) if appointment else None
    if patient and getattr(patient, 'convenio_id', None):
        return resolver_convenio(patient.convenio_id, loja_id=consulta.loja_id)
    return None


def _sync_primary_procedure(appointment, consulta) -> None:
    first_ap = appointment.appointment_procedures.order_by('ordem', 'id').first()
    new_proc = first_ap.procedure if first_ap else None
    new_id = new_proc.id if new_proc else None

    if appointment.procedure_id != new_id:
        appointment.procedure = new_proc
        appointment.save(update_fields=['procedure', 'updated_at'])

    if consulta.procedure_id != new_id:
        consulta.procedure = new_proc
        consulta.save(update_fields=['procedure', 'updated_at'])


def _garantir_procedimentos_legacy(appointment) -> None:
    """Migra procedimento único legado para appointment_procedures."""
    if appointment.appointment_procedures.exists():
        return
    if not appointment.procedure_id:
        return
    convenio = getattr(appointment, 'convenio', None)
    valor = resolver_preco_procedimento(convenio, appointment.procedure)
    AppointmentProcedure.objects.create(
        appointment=appointment,
        procedure=appointment.procedure,
        ordem=0,
        valor=valor,
        loja_id=appointment.loja_id,
    )


def adicionar_procedimento_consulta(consulta: Consulta, procedure_id: int) -> AppointmentProcedure:
    if consulta.status != 'IN_PROGRESS':
        raise ValueError('Só é possível adicionar procedimentos com a consulta em atendimento.')

    appointment = consulta.appointment
    _garantir_procedimentos_legacy(appointment)
    if appointment.appointment_procedures.filter(procedure_id=procedure_id).exists():
        raise ValueError('Este procedimento já está no atendimento.')

    try:
        procedure = Procedure.objects.get(pk=procedure_id, is_active=True)
    except Procedure.DoesNotExist as exc:
        raise ValueError('Procedimento não encontrado.') from exc

    convenio = _resolver_convenio_consulta(consulta)
    valor = resolver_preco_procedimento(convenio, procedure)
    max_ordem = appointment.appointment_procedures.aggregate(m=Max('ordem'))['m'] or 0

    ap = AppointmentProcedure.objects.create(
        appointment=appointment,
        procedure=procedure,
        ordem=max_ordem + 1,
        valor=valor,
        loja_id=consulta.loja_id,
    )
    _sync_primary_procedure(appointment, consulta)

    if procedure.termo_consentimento_ativo and (procedure.termo_consentimento or '').strip():
        garantir_termos_procedimento(consulta)

    _reabrir_recebimento_apos_procedimento(consulta)

    return ap


def remover_procedimento_consulta(consulta: Consulta, appointment_procedure_id: int) -> None:
    if consulta.status != 'IN_PROGRESS':
        raise ValueError('Não é possível remover procedimentos após finalizar a consulta.')

    appointment = consulta.appointment
    try:
        ap = AppointmentProcedure.objects.select_related('procedure').get(
            pk=appointment_procedure_id,
            appointment=appointment,
        )
    except AppointmentProcedure.DoesNotExist as exc:
        raise ValueError('Procedimento do atendimento não encontrado.') from exc

    procedure_id = ap.procedure_id
    ap.delete()

    ConsultaTermoProcedimento.objects.filter(
        consulta=consulta,
        procedure_id=procedure_id,
        status_assinatura_termo__in=('rascunho', 'aguardando_paciente'),
    ).delete()

    _sync_primary_procedure(appointment, consulta)
    garantir_termos_procedimento(consulta)
