"""
Sincronização de Consulta com mudanças de status do agendamento na agenda.
A consulta só é criada/atualizada quando o status muda na agenda — não manualmente na listagem.
"""
import logging
from decimal import Decimal

from django.utils.timezone import now

from .models import Appointment, Consulta, Payment

logger = logging.getLogger(__name__)


def _valor_consulta(appointment):
    """Valor padrão da taxa de consulta ao criar registro (procedimentos têm valores à parte)."""
    if appointment.appointment_procedures.exists():
        return Decimal('0')
    try:
        return appointment.procedure.preco or Decimal('0')
    except Exception:
        return Decimal('0')


def _valor_pagamento_padrao(appointment, consulta):
    """Total do pagamento = taxa de consulta + soma dos procedimentos vinculados."""
    vc = Decimal(str(consulta.valor_consulta or 0))
    return vc + appointment.valor_total


def sync_consulta_from_appointment_status(appointment, new_status, old_status=None):
    """
    Cria ou atualiza Consulta conforme o novo status do agendamento.
    Retorna a Consulta afetada ou None.
    """
    if new_status == old_status:
        return getattr(appointment, 'consulta', None)

    ts = now()

    if new_status == 'CONFIRMED':
        consulta, created = Consulta.objects.get_or_create(
            appointment=appointment,
            defaults={
                'patient_id': appointment.patient_id,
                'professional_id': appointment.professional_id,
                'procedure_id': appointment.procedure_id,
                'status': 'SCHEDULED',
                'valor_consulta': _valor_consulta(appointment),
                'convenio_id': appointment.convenio_id,
                'loja_id': appointment.loja_id,
            },
        )
        if not created and consulta.status not in ('IN_PROGRESS', 'COMPLETED'):
            consulta.status = 'SCHEDULED'
            consulta.save(update_fields=['status', 'updated_at'])
        return consulta

    if new_status == 'IN_PROGRESS':
        consulta, created = Consulta.objects.get_or_create(
            appointment=appointment,
            defaults={
                'patient_id': appointment.patient_id,
                'professional_id': appointment.professional_id,
                'procedure_id': appointment.procedure_id,
                'status': 'IN_PROGRESS',
                'data_inicio': ts,
                'valor_consulta': _valor_consulta(appointment),
                'convenio_id': appointment.convenio_id,
                'loja_id': appointment.loja_id,
            },
        )
        if not created:
            consulta.status = 'IN_PROGRESS'
            if not consulta.data_inicio:
                consulta.data_inicio = ts
            consulta.save(update_fields=['status', 'data_inicio', 'updated_at'])
        return consulta

    if new_status == 'COMPLETED':
        try:
            consulta = appointment.consulta
        except Consulta.DoesNotExist:
            consulta = Consulta.objects.create(
                appointment=appointment,
                patient_id=appointment.patient_id,
                professional_id=appointment.professional_id,
                procedure_id=appointment.procedure_id,
                status='COMPLETED',
                data_inicio=ts,
                data_fim=ts,
                valor_consulta=_valor_consulta(appointment),
                convenio_id=appointment.convenio_id,
                loja_id=appointment.loja_id,
            )
            return consulta
        consulta.status = 'COMPLETED'
        if not consulta.data_inicio:
            consulta.data_inicio = ts
        consulta.data_fim = ts
        consulta.save(update_fields=['status', 'data_inicio', 'data_fim', 'updated_at'])
        return consulta

    if new_status in ('CANCELLED', 'NO_SHOW'):
        try:
            consulta = appointment.consulta
        except Consulta.DoesNotExist:
            return None
        consulta.status = 'CANCELLED'
        consulta.save(update_fields=['status', 'updated_at'])
        return consulta

    return None


def criar_consulta_avulsa(
    *,
    patient,
    professional,
    procedure=None,
    procedures=None,
    loja_id=None,
    iniciar=False,
    local_atendimento_id=None,
    valor_consulta=None,
    convenio_id=None,
):
    """
    Cria uma consulta "avulsa" (sem agendamento prévio na agenda), a partir do
    cadastro do cliente. Gera o Appointment correspondente e a Consulta vinculada.

    Suporta múltiplos procedimentos via `procedures` (lista de Procedure).
    Se `procedures` não for passado, usa `procedure` (retrocompatível).

    Se `local_atendimento_id` for informado, associa o local à consulta e usa
    seu valor_consulta como padrão (caso `valor_consulta` não seja fornecido).
    Se `valor_consulta` for fornecido explicitamente (override), usa esse valor.

    Retorna a Consulta criada.
    """
    from .models import LocalAtendimento
    from .convenio_service import resolver_convenio, criar_appointment_procedures

    ts = now()
    status_inicial = 'IN_PROGRESS' if iniciar else 'SCHEDULED'
    loja_id = loja_id or getattr(patient, 'loja_id', None)

    # Resolve lista de procedimentos
    proc_list = procedures or ([procedure] if procedure else [])
    if not proc_list:
        raise ValueError('Informe pelo menos um procedimento.')
    primary_procedure = proc_list[0]

    # Resolve local de atendimento
    local_atendimento = None
    if local_atendimento_id:
        try:
            local_atendimento = LocalAtendimento.objects.get(pk=local_atendimento_id, is_active=True)
        except LocalAtendimento.DoesNotExist:
            local_atendimento = None

    convenio = resolver_convenio(convenio_id, loja_id=loja_id)
    if convenio is None and getattr(patient, 'convenio_id', None):
        convenio = resolver_convenio(patient.convenio_id, loja_id=loja_id)

    appointment = Appointment.objects.create(
        date=ts,
        status=status_inicial,
        patient=patient,
        professional=professional,
        procedure=primary_procedure,
        convenio=convenio,
        loja_id=loja_id,
    )
    criar_appointment_procedures(appointment, proc_list, convenio=convenio)

    # Determinar valor da consulta:
    # 1. Se valor_consulta fornecido explicitamente (override), usar esse
    # 2. Se local_atendimento informado, usar valor do local
    # 3. Caso contrário, usar valor total dos procedimentos (comportamento original)
    if valor_consulta is not None and Decimal(str(valor_consulta)) > 0:
        valor_final = Decimal(str(valor_consulta))
    elif local_atendimento:
        valor_final = local_atendimento.valor_consulta
    else:
        valor_final = appointment.valor_total

    consulta = Consulta.objects.create(
        appointment=appointment,
        patient=patient,
        professional=professional,
        procedure=primary_procedure,
        status=status_inicial,
        data_inicio=ts if iniciar else None,
        valor_consulta=valor_final,
        local_atendimento=local_atendimento,
        convenio=convenio,
        loja_id=loja_id,
    )
    return consulta


def _ensure_payment_for_appointment(appointment, consulta, *, payment_method=None, mark_as_paid=False, amount=None):
    """Garante lançamento financeiro do atendimento (cria ou atualiza)."""
    payment = Payment.objects.filter(appointment=appointment).first()
    valor = amount if amount is not None else _valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor, (int, float, str)):
        valor = Decimal(str(valor))

    # Resolver comissão do profissional
    local_id = consulta.local_atendimento_id if consulta else None
    comissao_pct, comissao_val = _resolver_comissao(
        appointment.professional, appointment.procedure, valor, local_id,
    )

    if not payment:
        return Payment.objects.create(
            appointment=appointment,
            amount=valor,
            payment_method=payment_method or 'CASH',
            status='PAID' if mark_as_paid else 'PENDING',
            payment_date=now() if mark_as_paid else None,
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )

    if payment_method:
        payment.payment_method = payment_method
    if amount is not None:
        payment.amount = valor
    if mark_as_paid:
        payment.status = 'PAID'
        if not payment.payment_date:
            payment.payment_date = now()
    # Atualizar comissão se ainda era 0
    if payment.comissao_percentual == 0 and payment.comissao_valor == 0:
        payment.comissao_percentual = comissao_pct
        payment.comissao_valor = comissao_val
    payment.save()
    return payment


def _resolver_comissao(professional, procedure, valor_pagamento, local_atendimento_id=None):
    """
    Resolve a comissão aplicável ao profissional para este atendimento.
    Prioridade: procedimento > consulta por local de atendimento.
    Retorna (percentual: int, valor: Decimal).
    """
    from .models import ProfessionalCommission

    if not professional:
        return 0, Decimal('0')

    # 1. Comissão por procedimento específico
    if procedure:
        comissao = ProfessionalCommission.objects.filter(
            professional=professional,
            tipo='procedimento',
            procedure=procedure,
            is_active=True,
        ).first()
        if comissao:
            return _calcular_comissao(comissao, valor_pagamento)

    # 2. Comissão por consulta no local
    if local_atendimento_id:
        comissao = ProfessionalCommission.objects.filter(
            professional=professional,
            tipo='consulta',
            local_atendimento_id=local_atendimento_id,
            is_active=True,
        ).first()
        if comissao:
            return _calcular_comissao(comissao, valor_pagamento)

    return 0, Decimal('0')


def _calcular_comissao(comissao, valor_pagamento):
    """Calcula percentual e valor da comissão baseado no modo (percentual ou fixo)."""
    if comissao.modo == 'percentual':
        pct = int(comissao.valor)
        val = (valor_pagamento * comissao.valor / Decimal('100')).quantize(Decimal('0.01'))
        return pct, val
    else:  # fixo
        return 0, comissao.valor


def iniciar_consulta(consulta):
    """
    Profissional inicia atendimento: consulta → IN_PROGRESS, agenda → IN_PROGRESS, data_inicio.
    """
    appointment = consulta.appointment
    if consulta.status != 'SCHEDULED':
        raise ValueError('A consulta precisa estar agendada para ser iniciada.')
    if appointment.status not in ('CONFIRMED', 'SCHEDULED'):
        raise ValueError('Confirme o agendamento na agenda antes de iniciar a consulta.')

    old_status = appointment.status
    ts = now()

    appointment.status = 'IN_PROGRESS'
    appointment.version = (appointment.version or 1) + 1
    appointment.save(update_fields=['status', 'version', 'updated_at'])

    consulta.status = 'IN_PROGRESS'
    consulta.data_inicio = ts
    consulta.save(update_fields=['status', 'data_inicio', 'updated_at'])

    sync_consulta_from_appointment_status(appointment, 'IN_PROGRESS', old_status)
    consulta.refresh_from_db()
    return consulta


def finalizar_consulta(consulta, *, payment_method=None, mark_as_paid=False, amount=None):
    """
    Finaliza consulta clínica: agenda → COMPLETED, consulta concluída e lançamento financeiro.
    """
    from rules.base import MotorRegras

    appointment = consulta.appointment
    old_status = appointment.status

    if consulta.status == 'COMPLETED':
        if appointment.status != 'COMPLETED':
            appointment.status = 'COMPLETED'
            appointment.version = (appointment.version or 1) + 1
            appointment.save(update_fields=['status', 'version', 'updated_at'])
            sync_consulta_from_appointment_status(appointment, 'COMPLETED', old_status)
        if not consulta.data_fim:
            consulta.data_fim = now()
            consulta.save(update_fields=['data_fim', 'updated_at'])
        try:
            MotorRegras().executar('AGENDAMENTO_FINALIZADO', {'appointment': appointment})
        except Exception:
            logger.exception('Erro ao executar regra financeira (consulta %s)', consulta.id)
        _ensure_payment_for_appointment(
            appointment, consulta,
            payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
        )
        consulta.refresh_from_db()
        return consulta

    if consulta.status != 'IN_PROGRESS':
        raise ValueError('Inicie a consulta antes de finalizar.')

    ts = now()

    appointment.status = 'COMPLETED'
    appointment.version = (appointment.version or 1) + 1
    appointment.save(update_fields=['status', 'version', 'updated_at'])

    consulta.status = 'COMPLETED'
    if not consulta.data_inicio:
        consulta.data_inicio = ts
    consulta.data_fim = ts
    consulta.save(update_fields=['status', 'data_inicio', 'data_fim', 'updated_at'])

    sync_consulta_from_appointment_status(appointment, 'COMPLETED', old_status)

    try:
        MotorRegras().executar('AGENDAMENTO_FINALIZADO', {'appointment': appointment})
    except Exception:
        logger.exception('Erro ao executar regra financeira (consulta %s)', consulta.id)

    _ensure_payment_for_appointment(
        appointment, consulta,
        payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
    )
    consulta.refresh_from_db()
    return consulta
