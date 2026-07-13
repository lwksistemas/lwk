from decimal import Decimal

from django.utils.timezone import now


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
    nome_agenda_id=None,
    appointment_date=None,
    notes=None,
    retorno_procedure_id=None,
):
    """Cria uma consulta "avulsa" (sem agendamento prévio na agenda), a partir do
    cadastro do cliente. Gera o Appointment correspondente e a Consulta vinculada.

    Suporta múltiplos procedimentos via `procedures` (lista de Procedure).
    Se `procedures` não for passado, usa `procedure` (retrocompatível).

    Se `local_atendimento_id` for informado, associa o local à consulta e usa
    seu valor_consulta como padrão (caso `valor_consulta` não seja fornecido).
    Se `valor_consulta` for fornecido explicitamente (override), usa esse valor.

    Retorna a Consulta criada.
    """
    from clinica_beleza import consulta_service

    from ..convenio_service import criar_appointment_procedures, resolver_convenio
    from ..models import LocalAtendimento, NomeAgenda, Procedure

    ts = appointment_date or now()
    loja_id = loja_id or getattr(patient, "loja_id", None)

    proc_list = procedures or ([procedure] if procedure else [])
    primary_procedure = proc_list[0] if proc_list else None

    local_atendimento = None
    if local_atendimento_id:
        try:
            local_atendimento = LocalAtendimento.objects.get(pk=local_atendimento_id, is_active=True)
        except LocalAtendimento.DoesNotExist:
            local_atendimento = None

    convenio = resolver_convenio(convenio_id, loja_id=loja_id)
    if convenio is None and getattr(patient, "convenio_id", None):
        convenio = resolver_convenio(patient.convenio_id, loja_id=loja_id)

    if iniciar:
        consulta_service.validar_paciente_sem_consulta_em_andamento(patient.id)

    nome_agenda = None
    if nome_agenda_id:
        nome_agenda = NomeAgenda.objects.filter(pk=nome_agenda_id, is_active=True).first()

    retorno_procedure = None
    if retorno_procedure_id:
        retorno_procedure = Procedure.objects.filter(pk=retorno_procedure_id, is_active=True).first()

    if valor_consulta is not None and Decimal(str(valor_consulta)) > 0:
        valor_final = Decimal(str(valor_consulta))
    elif local_atendimento:
        valor_final = Decimal(str(local_atendimento.valor_consulta or 0))
    else:
        valor_final = Decimal(0)

    if iniciar:
        appointment_status = "IN_PROGRESS"
        consulta_status = "IN_PROGRESS"
    else:
        appointment_status = "CONFIRMED"
        consulta_status = "RECEBER"

    appointment = consulta_service.Appointment.objects.create(
        date=ts,
        status=appointment_status,
        patient=patient,
        professional=professional,
        procedure=primary_procedure,
        convenio=convenio,
        local_atendimento=local_atendimento,
        nome_agenda=nome_agenda,
        retorno_procedure=retorno_procedure,
        notes=(notes or "").strip() or None,
        loja_id=loja_id,
    )
    if proc_list:
        criar_appointment_procedures(appointment, proc_list, convenio=convenio)

    consulta = consulta_service.Consulta.objects.create(
        appointment=appointment,
        patient=patient,
        professional=professional,
        procedure=primary_procedure,
        status=consulta_status,
        data_inicio=ts if iniciar else None,
        valor_consulta=valor_final,
        local_atendimento=local_atendimento,
        convenio=convenio,
        loja_id=loja_id,
    )
    from ..retorno_service import aplicar_retorno_em_consulta

    aplicar_retorno_em_consulta(consulta, appointment)
    consulta.refresh_from_db()
    if not iniciar:
        total = consulta_service._valor_pagamento_padrao(appointment, consulta)
        if consulta.retorno_gratuito or total <= 0:
            consulta.status = "SCHEDULED"
            consulta.save(update_fields=["status", "updated_at"])
    if consulta.status == "RECEBER":
        from .payment import garantir_conta_pendente_consulta
        garantir_conta_pendente_consulta(consulta)
    return consulta


def iniciar_consulta(consulta):
    """Profissional inicia atendimento: consulta → IN_PROGRESS, agenda → IN_PROGRESS, data_inicio.
    """
    from clinica_beleza import consulta_service

    appointment = consulta.appointment
    if consulta.status not in ("SCHEDULED", "RECEBER"):
        raise ValueError("A consulta precisa estar aguardando início ou recebimento para ser iniciada.")
    if appointment.status != "CONFIRMED":
        raise ValueError("Registre a chegada do cliente na agenda (status Cliente presente) antes de iniciar a consulta.")

    consulta_service.validar_paciente_sem_consulta_em_andamento(
        consulta.patient_id, exclude_consulta_id=consulta.id,
    )

    old_status = appointment.status
    ts = now()

    appointment.status = "IN_PROGRESS"
    appointment.date = ts
    appointment.version = (appointment.version or 1) + 1
    appointment.save(update_fields=["status", "date", "version", "updated_at"])

    consulta.status = "IN_PROGRESS"
    consulta.data_inicio = ts
    consulta.save(update_fields=["status", "data_inicio", "updated_at"])

    consulta_service.sync_consulta_from_appointment_status(appointment, "IN_PROGRESS", old_status)
    consulta.refresh_from_db()
    return consulta


def _publicar_ou_garantir_pagamento_ao_finalizar(
    consulta,
    appointment,
    *,
    payment_method=None,
    mark_as_paid=False,
    amount=None,
):
    """Publica DRAFT no Financeiro ou cria lançamento se ainda não houver PAID."""
    from clinica_beleza import consulta_service

    from ..models import Payment

    payment = Payment.objects.filter(appointment=appointment).first()
    if payment and payment.status == "DRAFT":
        consulta_service.publicar_pagamento_financeiro(consulta)
    elif not Payment.objects.filter(appointment=appointment, status="PAID").exists():
        consulta_service._ensure_payment_for_appointment(
            appointment, consulta,
            payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
        )


def finalizar_consulta(
    consulta,
    *,
    payment_method=None,
    mark_as_paid=False,
    amount=None,
    local_atendimento_id=None,
    skip_estoque=False,
):
    """Finaliza consulta clínica: agenda → COMPLETED, consulta concluída e lançamento financeiro.
    Baixa produtos do estoque registrados na consulta.
    """
    from clinica_beleza import consulta_service
    from rules.base import MotorRegras

    from ..estoque_service import baixar_produtos_consulta, produtos_estoque_insuficiente, tenant_atomic
    from ._deps import logger

    appointment = consulta.appointment
    old_status = appointment.status
    consulta_service._aplicar_local_na_consulta(consulta, local_atendimento_id)

    if consulta.status == "COMPLETED":
        if appointment.status != "COMPLETED":
            appointment.status = "COMPLETED"
            appointment.version = (appointment.version or 1) + 1
            appointment.save(update_fields=["status", "version", "updated_at"])
            consulta_service.sync_consulta_from_appointment_status(appointment, "COMPLETED", old_status)
        if not consulta.data_fim:
            consulta.data_fim = now()
            consulta.save(update_fields=["data_fim", "updated_at"])
        try:
            MotorRegras().executar("AGENDAMENTO_FINALIZADO", {"appointment": appointment})
        except Exception:
            logger.exception("Erro ao executar regra financeira (consulta %s)", consulta.id)
        _publicar_ou_garantir_pagamento_ao_finalizar(
            consulta, appointment,
            payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
        )
        consulta.refresh_from_db()
        return consulta

    if consulta.status not in ("IN_PROGRESS", "RECEBER"):
        raise ValueError("Inicie a consulta antes de finalizar.")
    if consulta.status == "RECEBER" and not consulta.data_inicio:
        raise ValueError("Inicie a consulta antes de finalizar.")

    if not skip_estoque:
        insuficientes = produtos_estoque_insuficiente(consulta)
        if insuficientes:
            linhas = "\n".join(f"• {msg}" for msg in insuficientes)
            raise ValueError(
                f"Estoque insuficiente para finalizar a consulta. Regularize o estoque ou "
                f"remova/ajuste os produtos registrados:\n{linhas}",
            )

    ts = now()

    with tenant_atomic():
        baixar_produtos_consulta(consulta)

    appointment.status = "COMPLETED"
    appointment.version = (appointment.version or 1) + 1
    appointment.save(update_fields=["status", "version", "updated_at"])

    consulta.status = "COMPLETED"
    if not consulta.data_inicio:
        consulta.data_inicio = ts
    consulta.data_fim = ts
    consulta.save(update_fields=["status", "data_inicio", "data_fim", "updated_at"])

    consulta_service.sync_consulta_from_appointment_status(appointment, "COMPLETED", old_status)

    try:
        MotorRegras().executar("AGENDAMENTO_FINALIZADO", {"appointment": appointment})
    except Exception:
        logger.exception("Erro ao executar regra financeira (consulta %s)", consulta.id)

    _publicar_ou_garantir_pagamento_ao_finalizar(
        consulta, appointment,
        payment_method=payment_method, mark_as_paid=mark_as_paid, amount=amount,
    )
    consulta.refresh_from_db()
    return consulta
