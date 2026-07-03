from decimal import Decimal

from django.utils.timezone import now

from ._deps import logger


def _tentar_nfse_pos_pagamento(consulta, payment):
    """Dispara emissão NFS-e após pagamento confirmado (não bloqueia fluxo)."""
    try:
        from ..nfse_consulta_service import tentar_emitir_nfse_consulta

        tentar_emitir_nfse_consulta(consulta, payment)
    except Exception:
        logger.exception('Erro ao tentar NFS-e após pagamento (consulta %s)', consulta.id)


def _ensure_payment_for_appointment(appointment, consulta, *, payment_method=None, mark_as_paid=False, amount=None):
    """Garante lançamento financeiro do atendimento (cria ou atualiza)."""
    from clinica_beleza import consulta_service

    consulta_service._garantir_valor_consulta_consulta(consulta)
    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    valor = amount if amount is not None else consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor, (int, float, str)):
        valor = Decimal(str(valor))

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor,
    )

    if not payment:
        payment = consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=valor,
            payment_method=payment_method or 'CASH',
            status='PAID' if mark_as_paid else 'PENDING',
            payment_date=now() if mark_as_paid else None,
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )
        if mark_as_paid:
            _tentar_nfse_pos_pagamento(consulta, payment)
        return payment

    if payment_method:
        payment.payment_method = payment_method
    if amount is not None:
        payment.amount = valor
    was_paid = payment.status == 'PAID'
    if mark_as_paid:
        payment.status = 'PAID'
        if not payment.payment_date:
            payment.payment_date = now()
    payment.comissao_percentual = comissao_pct
    payment.comissao_valor = comissao_val
    payment.save()
    if mark_as_paid and not was_paid:
        _tentar_nfse_pos_pagamento(consulta, payment)
    return payment
