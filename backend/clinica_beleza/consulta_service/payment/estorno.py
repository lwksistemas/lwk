from decimal import Decimal

from .._deps import logger
from ._common import _tenant_atomic
from .receber import _atualizar_status_consulta_apos_recebimento


@_tenant_atomic
def estornar_recebimento_consulta(consulta):
    """Estorna lançamentos de pagamento de uma consulta ainda não finalizada.

    - Cancela PaymentParcela (PAID → CANCELLED)
    - Zera Payment (PENDING, amount=0) e restaura valor_total bruto
    - Sem atendimento iniciado: volta para RECEBER
    - Já em atendimento (data_inicio): mantém IN_PROGRESS para não sumir da fila
    """
    from clinica_beleza import consulta_service

    from ...models.financeiro import PaymentParcela

    if consulta.status == "COMPLETED":
        raise ValueError(
            "Consulta já finalizada. Correções de pagamento devem ser feitas no Financeiro.",
        )
    if consulta.status == "CANCELLED":
        raise ValueError("Consulta cancelada não permite estorno de pagamento.")

    appointment = getattr(consulta, "appointment", None)
    if not appointment:
        raise ValueError("Consulta sem agendamento vinculado.")

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment:
        raise ValueError("Nenhum pagamento encontrado para estornar.")

    try:
        ja_pago = payment.valor_pago_parcelas
    except (TypeError, ArithmeticError) as exc:
        logger.warning("Erro valor_pago_parcelas payment %s: %s", payment.pk, exc)
        ja_pago = Decimal(str(payment.amount or 0))
    if ja_pago <= 0 and payment.status == "PENDING":
        raise ValueError("Não há valor pago para estornar.")

    PaymentParcela.objects.filter(payment=payment, status="PAID").update(status="CANCELLED")

    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_bruto = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor_bruto, (int, float, str)):
        valor_bruto = Decimal(str(valor_bruto))

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_bruto if valor_bruto > 0 else Decimal(0),
    )

    payment.status = "PENDING"
    payment.amount = Decimal(0)
    payment.valor_total = valor_bruto
    payment.payment_date = None
    payment.notes = None
    payment.comissao_percentual = comissao_pct
    payment.comissao_valor = comissao_val
    payment.save(update_fields=[
        "status", "amount", "valor_total", "payment_date", "notes",
        "comissao_percentual", "comissao_valor", "updated_at",
    ])

    if consulta.status not in ("COMPLETED", "CANCELLED"):
        _atualizar_status_consulta_apos_recebimento(consulta, payment)

    return payment
