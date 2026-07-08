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


def _atualizar_status_consulta_apos_recebimento(consulta, payment) -> None:
    """Após recebimento: SCHEDULED se quitou e não iniciou; IN_PROGRESS se já em atendimento."""
    try:
        saldo = payment.saldo_devedor
    except Exception:
        saldo = Decimal('0')

    if saldo > 0:
        consulta.status = 'RECEBER'
    elif consulta.data_inicio:
        consulta.status = 'IN_PROGRESS'
    else:
        consulta.status = 'SCHEDULED'
    consulta.save(update_fields=['status', 'updated_at'])


def _reabrir_recebimento_apos_procedimento(consulta) -> None:
    """Se procedimento extra aumenta total após pagamento quitado, volta para RECEBER."""
    from clinica_beleza import consulta_service

    appointment = consulta.appointment
    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment or payment.status != 'PAID':
        return

    consulta_service._garantir_valor_consulta_consulta(consulta)
    novo_total = consulta_service._valor_pagamento_padrao(appointment, consulta)
    pago = payment.valor_pago_parcelas if payment.parcelas.exists() else Decimal(str(payment.amount or 0))
    if novo_total <= pago:
        return

    payment.valor_total = novo_total
    payment.status = 'PARTIAL' if pago > 0 else 'PENDING'
    payment.amount = pago
    payment.save(update_fields=['valor_total', 'status', 'amount', 'updated_at'])
    consulta.status = 'RECEBER'
    consulta.save(update_fields=['status', 'updated_at'])


def registrar_recebimento_consulta(
    consulta,
    *,
    payment_method='CASH',
    amount=None,
    mark_as_paid=False,
):
    """
    Registra recebimento na consulta (total ou parcial).
    Retorna Payment atualizado.
    """
    from clinica_beleza import consulta_service
    from ..models.financeiro import PaymentParcela

    if consulta.status in ('COMPLETED', 'CANCELLED'):
        raise ValueError('Consulta não está aberta para recebimento.')

    appointment = consulta.appointment
    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_total = consulta_service._valor_pagamento_padrao(appointment, consulta)

    if amount is None:
        valor_recebido = valor_total
    else:
        valor_recebido = Decimal(str(amount))
    if valor_recebido <= 0:
        raise ValueError('Valor deve ser maior que zero.')

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_total,
    )

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    ts = now()

    if not payment:
        payment = consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=Decimal('0'),
            valor_total=valor_total,
            payment_method=payment_method,
            status='PENDING',
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )
    else:
        payment.valor_total = valor_total
        payment.payment_method = payment_method
        payment.comissao_percentual = comissao_pct
        payment.comissao_valor = comissao_val

    try:
        saldo = payment.saldo_devedor
    except Exception:
        saldo = valor_total

    if mark_as_paid and valor_recebido >= saldo:
        if payment.parcelas.exists():
            restante = saldo
            if restante > 0:
                PaymentParcela.objects.create(
                    payment=payment,
                    valor=restante,
                    payment_method=payment_method,
                    payment_date=ts.date(),
                    loja_id=payment.loja_id,
                )
            payment.amount = payment.valor_pago_parcelas
        else:
            payment.amount = valor_recebido
        payment.status = 'PAID'
        payment.payment_date = ts
        payment.save(update_fields=[
            'amount', 'valor_total', 'payment_method', 'status', 'payment_date',
            'comissao_percentual', 'comissao_valor', 'updated_at',
        ])
        _tentar_nfse_pos_pagamento(consulta, payment)
    else:
        PaymentParcela.objects.create(
            payment=payment,
            valor=valor_recebido,
            payment_method=payment_method,
            payment_date=ts.date(),
            loja_id=payment.loja_id,
        )
        total_pago = payment.valor_pago_parcelas
        if total_pago >= valor_total:
            payment.status = 'PAID'
            payment.amount = total_pago
            payment.payment_date = ts
            _tentar_nfse_pos_pagamento(consulta, payment)
        else:
            payment.status = 'PARTIAL'
            payment.amount = total_pago
        payment.save(update_fields=[
            'amount', 'valor_total', 'payment_method', 'status', 'payment_date',
            'comissao_percentual', 'comissao_valor', 'updated_at',
        ])

    _atualizar_status_consulta_apos_recebimento(consulta, payment)
    return payment
