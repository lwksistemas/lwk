from decimal import Decimal

from core.decimal_utils import to_decimal


def aplicar_valor_procedimentos_atendimento(appointment, novo_valor) -> Decimal:
    """Atualiza o valor dos procedimentos do atendimento (override em AppointmentProcedure)."""
    valor = to_decimal(novo_valor, "valor_procedimentos")
    if valor is None:
        raise ValueError("Valor do procedimento inválido.")
    if valor < 0:
        raise ValueError("Valor do procedimento não pode ser negativo.")

    linhas = list(
        appointment.appointment_procedures.select_related("procedure").order_by("ordem", "id"),
    )
    if not linhas:
        if not getattr(appointment, "procedure_id", None):
            raise ValueError("Não há procedimento neste atendimento para alterar o valor.")
        from clinica_beleza.models import AppointmentProcedure

        AppointmentProcedure.objects.create(
            appointment=appointment,
            procedure_id=appointment.procedure_id,
            valor=valor,
            ordem=0,
            loja_id=appointment.loja_id,
        )
    elif len(linhas) == 1:
        linhas[0].valor = valor
        linhas[0].save(update_fields=["valor"])
    else:
        atuais = [Decimal(str(ap.get_valor() or 0)) for ap in linhas]
        soma = sum(atuais)
        restante = valor
        total_linhas = len(linhas)
        for i, ap in enumerate(linhas):
            if i == total_linhas - 1:
                ap.valor = restante
            elif soma <= 0:
                ap.valor = valor if i == 0 else Decimal("0")
                if i == 0:
                    restante = Decimal("0")
            else:
                parte = (atuais[i] / soma * valor).quantize(Decimal("0.01"))
                ap.valor = parte
                restante -= parte
            ap.save(update_fields=["valor"])

    appointment._valor_total_cache = None
    return valor


def _consulta_defaults_from_appointment(appointment, **extra):
    """Campos comuns ao criar Consulta a partir de um Appointment."""
    from clinica_beleza import consulta_service

    from ..retorno_service import valor_consulta_com_retorno

    valor_base = consulta_service._valor_consulta(appointment)
    valor_ajustado, retorno = valor_consulta_com_retorno(appointment, valor_base)
    defaults = {
        "patient_id": appointment.patient_id,
        "professional_id": appointment.professional_id,
        "procedure_id": appointment.procedure_id,
        "valor_consulta": valor_ajustado,
        "retorno_gratuito": retorno.elegivel,
        "retorno_tipo": retorno.tipo or "",
        "convenio_id": appointment.convenio_id,
        "loja_id": appointment.loja_id,
    }
    if getattr(appointment, "local_atendimento_id", None):
        defaults["local_atendimento_id"] = appointment.local_atendimento_id
    defaults.update(extra)
    return defaults


def _valor_consulta(appointment, consulta=None):
    """Valor padrão da taxa de consulta ao criar registro (procedimentos têm valores à parte)."""
    if consulta is not None:
        local = getattr(consulta, "local_atendimento", None)
        if local is not None:
            return Decimal(str(local.valor_consulta or 0))
    local_appt = getattr(appointment, "local_atendimento", None)
    if local_appt is not None:
        return Decimal(str(local_appt.valor_consulta or 0))
    if appointment.appointment_procedures.exists():
        return Decimal(0)
    try:
        return appointment.procedure.preco or Decimal(0)
    except Exception:
        return Decimal(0)


def _garantir_valor_consulta_consulta(consulta) -> None:
    """Persiste taxa de consulta a partir do local quando ainda está zerada."""
    if getattr(consulta, "retorno_gratuito", False):
        return
    if Decimal(str(consulta.valor_consulta or 0)) > 0:
        return
    local = getattr(consulta, "local_atendimento", None)
    if local is None:
        return
    local_vc = Decimal(str(local.valor_consulta or 0))
    if local_vc <= 0:
        return
    consulta.valor_consulta = local_vc
    consulta.save(update_fields=["valor_consulta", "updated_at"])


def _aplicar_local_na_consulta(consulta, local_atendimento_id=None) -> None:
    """Associa local de atendimento à consulta antes do lançamento financeiro."""
    if not local_atendimento_id or consulta.local_atendimento_id:
        return
    from ..models import LocalAtendimento

    try:
        local = LocalAtendimento.objects.get(pk=local_atendimento_id, is_active=True)
    except LocalAtendimento.DoesNotExist:
        raise ValueError("Local de atendimento inválido.")

    consulta.local_atendimento = local
    if Decimal(str(consulta.valor_consulta or 0)) <= 0:
        consulta.valor_consulta = Decimal(str(local.valor_consulta or 0))
    consulta.save(update_fields=["local_atendimento", "valor_consulta", "updated_at"])


def _valor_pagamento_padrao(appointment, consulta):
    """Total do pagamento = taxa de consulta + soma dos procedimentos vinculados."""
    vc = Decimal(str(consulta.valor_consulta or 0))
    return vc + appointment.valor_total
