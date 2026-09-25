from decimal import Decimal

from django.db import transaction
from django.utils.timezone import now

from .._deps import logger
from ._common import (
    _METODOS_VALIDOS,
    _calcular_valor_total_com_desconto,
    _finalizar_payment_draft,
    _garantir_ou_criar_payment,
    _log_movimento_financeiro,
    _normalize_entradas,
    _tenant_atomic,
    _tentar_nfse_pos_pagamento,
    _validar_prazo_paciente_para_entradas,
)


def _agendar_nfse_pos_pagamento(consulta, payment):
    """Emite a NFS-e só depois do commit. Rollback não deixa nota emitida."""
    from tenants.middleware import get_current_tenant_db

    using = get_current_tenant_db() or "default"

    def _emitir_nfse():
        _tentar_nfse_pos_pagamento(consulta, payment)

    transaction.on_commit(_emitir_nfse, using=using)


def _ensure_payment_for_appointment(
    appointment, consulta, *, payment_method=None, mark_as_paid=False, amount=None, usuario=None,
):
    """Garante lançamento financeiro do atendimento (cria ou atualiza)."""
    from clinica_beleza import consulta_service

    _invalidar_totais_agendamento(appointment)
    consulta_service._garantir_valor_consulta_consulta(consulta)
    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    valor = amount if amount is not None else consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor, (int, float, str)):
        valor = Decimal(str(valor))

    # Retorno zera só a taxa: com procedimento cobrado ainda há valor a receber.
    # Não marcar PAID automático em atendimento isento (R$ 0) sem recebimento real.
    if valor <= 0:
        mark_as_paid = False

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor,
    )

    if not payment:
        payment = consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=Decimal(0) if not mark_as_paid else valor,
            valor_total=valor,
            payment_method=payment_method or "CASH",
            status="PAID" if mark_as_paid else "PENDING",
            payment_date=now() if mark_as_paid else None,
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )
        if mark_as_paid:
            _log_movimento_financeiro("Pagamento lançado", consulta, payment, usuario)
            _agendar_nfse_pos_pagamento(consulta, payment)
        return payment

    if payment_method:
        payment.payment_method = payment_method
    if amount is not None:
        payment.amount = valor
    if payment.valor_total is None or Decimal(str(payment.valor_total or 0)) <= 0:
        payment.valor_total = valor
    was_paid = payment.status == "PAID"
    if mark_as_paid:
        payment.status = "PAID"
        if not payment.payment_date:
            payment.payment_date = now()
    payment.comissao_percentual = comissao_pct
    payment.comissao_valor = comissao_val
    payment.save()
    if mark_as_paid and not was_paid:
        _log_movimento_financeiro("Pagamento lançado", consulta, payment, usuario)
        _agendar_nfse_pos_pagamento(consulta, payment)
    return payment


def garantir_conta_pendente_consulta(consulta) -> None:
    """Cria conta a receber (Payment PENDING) quando a consulta está em RECEBER."""
    if consulta.status != "RECEBER":
        return
    try:
        _garantir_conta_pendente_consulta_inner(consulta)
    except Exception:
        logger.exception(
            "Falha ao garantir conta pendente (consulta %s) — consulta mantida em RECEBER",
            getattr(consulta, "id", None),
        )


def _garantir_conta_pendente_consulta_inner(consulta) -> None:
    from clinica_beleza import consulta_service

    appointment = getattr(consulta, "appointment", None)
    if not appointment:
        return

    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_total = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if valor_total <= 0:
        return

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_total,
    )

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment:
        consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=Decimal(0),
            valor_total=valor_total,
            payment_method="CASH",
            status="PENDING",
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
        )
        return

    if payment.status in ("PENDING", "PARTIAL", "DRAFT"):
        payment.valor_total = valor_total
        payment.comissao_percentual = comissao_pct
        payment.comissao_valor = comissao_val
        payment.save(update_fields=[
            "valor_total", "comissao_percentual", "comissao_valor", "updated_at",
        ])


def _atualizar_status_consulta_apos_recebimento(consulta, payment) -> None:
    """Após recebimento: SCHEDULED se quitou e não iniciou; IN_PROGRESS se já em atendimento.

    Se já iniciou (data_inicio) e o saldo ainda está aberto, mantém IN_PROGRESS —
    o botão Receber usa saldo/payment_status, não precisa rebaixar para RECEBER.
    """
    try:
        quitado = payment.saldo_devedor <= Decimal("0.01")
    except (TypeError, ArithmeticError) as exc:
        logger.warning("Erro saldo_devedor payment %s: %s", payment.pk, exc)
        quitado = payment.status in ("PAID", "DRAFT") and Decimal(str(payment.amount or 0)) > 0

    if getattr(consulta, "data_inicio", None):
        consulta.status = "IN_PROGRESS"
    elif not quitado:
        consulta.status = "RECEBER"
    else:
        consulta.status = "SCHEDULED"
    consulta.save(update_fields=["status", "updated_at"])


def _status_rascunho_ou_financeiro(consulta, *, quitado: bool, tem_pago: bool) -> str:
    """Antes de finalizar: DRAFT. Após finalizar: PAID/PARTIAL/PENDING."""
    if getattr(consulta, "status", None) == "COMPLETED":
        if quitado:
            return "PAID"
        return "PARTIAL" if tem_pago else "PENDING"
    if tem_pago:
        return "DRAFT"
    return "PENDING"


def _invalidar_totais_agendamento(appointment) -> None:
    """A view da consulta pré-carrega os procedimentos. Sem isso, o total ignora o item recém-incluído."""
    appointment._valor_total_cache = None
    cache = getattr(appointment, "_prefetched_objects_cache", None)
    if isinstance(cache, dict):
        cache.pop("appointment_procedures", None)


def _sincronizar_recebimento_apos_procedimento(consulta) -> None:
    """Após incluir/remover procedimento: atualiza valor_total do Payment.
    Se total sobe após quitado → saldo em aberto (parcial); se total cai e cobre o pago → rascunho/PAID.
    """
    from clinica_beleza import consulta_service

    appointment = getattr(consulta, "appointment", None)
    if not appointment:
        return
    _invalidar_totais_agendamento(appointment)

    payment = consulta_service.Payment.objects.filter(appointment=appointment).first()
    if not payment or payment.status == "CANCELLED":
        return

    consulta_service._garantir_valor_consulta_consulta(consulta)
    novo_total = consulta_service._valor_pagamento_padrao(appointment, consulta)
    pago = payment.valor_pago_parcelas

    payment.valor_total = novo_total
    # Total 0 (retorno sem procedimento) não é quitação: evita PAID fantasma no Financeiro.
    if novo_total <= 0:
        quitado, tem_pago = False, pago > 0
    elif pago >= novo_total:
        quitado, tem_pago = True, True
    else:
        quitado, tem_pago = False, pago > 0

    payment.status = _status_rascunho_ou_financeiro(consulta, quitado=quitado, tem_pago=tem_pago)
    payment.amount = pago
    if payment.status in ("DRAFT", "PENDING"):
        payment.payment_date = None
    payment.save(update_fields=["valor_total", "status", "amount", "payment_date", "updated_at"])
    if consulta.status not in ("COMPLETED", "CANCELLED"):
        _atualizar_status_consulta_apos_recebimento(consulta, payment)


@_tenant_atomic
def registrar_recebimento_consulta(
    consulta,
    *,
    payment_method="CASH",
    amount=None,
    mark_as_paid=False,
    desconto=None,
    entradas=None,
    valor_procedimentos=None,
    usuario=None,
):
    """Registra recebimento na consulta (total ou parcial) como rascunho (DRAFT).

    Só entra no Financeiro (PAID/PARTIAL + payment_date + NFS-e) ao finalizar a consulta.
    """
    from clinica_beleza import consulta_service
    from clinica_beleza.models import Consulta

    # Lock só na Consulta (of=self): Postgres rejeita FOR UPDATE no lado nullable do OUTER JOIN.
    consulta = (
        Consulta.objects.select_for_update(of=("self",))
        .select_related("appointment", "appointment__professional", "patient")
        .get(pk=consulta.pk)
    )

    if consulta.status in ("COMPLETED", "CANCELLED"):
        raise ValueError("Consulta não está aberta para recebimento.")

    appointment = consulta.appointment
    consulta_service._garantir_valor_consulta_consulta(consulta)
    if valor_procedimentos not in (None, ""):
        consulta_service.aplicar_valor_procedimentos_atendimento(appointment, valor_procedimentos)
    valor_bruto = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor_bruto, (int, float, str)):
        valor_bruto = Decimal(str(valor_bruto))

    payment = (
        consulta_service.Payment.objects.select_for_update(of=("self",))
        .filter(appointment=appointment)
        .first()
    )
    valor_total = _calcular_valor_total_com_desconto(valor_bruto, desconto, payment)
    valor_desconto = valor_bruto - valor_total

    if valor_total <= 0:
        if valor_desconto <= 0:
            raise ValueError("Valor deve ser maior que zero.")
        lista = []
        soma_entradas = Decimal(0)
        mark_as_paid = True
        metodo_principal = "CASH"
    else:
        lista = _normalize_entradas(entradas, payment_method=payment_method, amount=amount)
        if lista is None:
            metodo = (payment_method or "CASH").strip().upper() or "CASH"
            if metodo not in _METODOS_VALIDOS:
                raise ValueError("Forma de pagamento inválida.")
            lista = [{"payment_method": metodo, "valor": valor_total}]

        soma_entradas = sum((e["valor"] for e in lista), Decimal(0))
        if soma_entradas <= 0:
            raise ValueError("Valor deve ser maior que zero.")
        metodo_principal = lista[-1]["payment_method"]

    # Bloqueia recebimento a prazo se o paciente não tem política configurada pelo admin.
    _validar_prazo_paciente_para_entradas(consulta, lista)

    comissao_pct, comissao_val = consulta_service.calcular_comissao_payment_atendimento(
        appointment=appointment,
        consulta=consulta,
        amount=valor_total if valor_total > 0 else valor_bruto,
    )

    ts = now()
    payment = _garantir_ou_criar_payment(
        consulta_service, appointment, valor_total, metodo_principal,
        comissao_pct, comissao_val, valor_desconto, payment,
    )

    try:
        saldo = payment.saldo_devedor
    except (TypeError, ArithmeticError) as exc:
        logger.warning("Erro saldo_devedor payment %s: %s", payment.pk, exc)
        saldo = valor_total
    if soma_entradas > saldo + Decimal("0.01"):
        raise ValueError(f"Soma das formas (R$ {soma_entradas}) excede o saldo a receber (R$ {saldo}).")

    _finalizar_payment_draft(payment, valor_total, lista, valor_desconto, mark_as_paid, ts)
    _atualizar_status_consulta_apos_recebimento(consulta, payment)
    _log_movimento_financeiro("Recebimento registrado", consulta, payment, usuario)
    return payment


@_tenant_atomic
def publicar_pagamento_financeiro(consulta, *, usuario=None):
    """Publica o rascunho de pagamento no Financeiro ao finalizar a consulta.

    DRAFT → PAID/PARTIAL + payment_date; dispara NFS-e se quitado.
    """
    from clinica_beleza import consulta_service
    from clinica_beleza.models import Consulta

    consulta = (
        Consulta.objects.select_for_update(of=("self",))
        .select_related("appointment")
        .get(pk=consulta.pk)
    )
    appointment = getattr(consulta, "appointment", None)
    if not appointment:
        return None

    payment = (
        consulta_service.Payment.objects.select_for_update(of=("self",))
        .filter(appointment=appointment)
        .first()
    )
    if not payment or payment.status == "CANCELLED":
        return payment

    # Recalcula total se o lançamento ficou zerado (ex.: retorno aplicado antes do procedimento).
    _invalidar_totais_agendamento(appointment)
    consulta_service._garantir_valor_consulta_consulta(consulta)
    valor_atual = consulta_service._valor_pagamento_padrao(appointment, consulta)
    if isinstance(valor_atual, (int, float, str)):
        valor_atual = Decimal(str(valor_atual))
    valor_salvo = payment.valor_total_efetivo
    if isinstance(valor_salvo, (int, float, str)):
        valor_salvo = Decimal(str(valor_salvo or 0))
    if valor_atual > 0 and valor_salvo <= 0:
        payment.valor_total = valor_atual
        payment.save(update_fields=["valor_total", "updated_at"])

    if payment.status not in ("DRAFT", "PENDING", "PARTIAL"):
        # Já publicado (PAID) — nada a fazer
        if payment.status == "PAID" and not payment.payment_date:
            payment.payment_date = now()
            payment.save(update_fields=["payment_date", "updated_at"])
        return payment

    total_pago = payment.valor_pago_parcelas
    valor_total = payment.valor_total_efetivo
    if isinstance(valor_total, (int, float, str)):
        valor_total = Decimal(str(valor_total))

    ts = now()

    if total_pago <= 0 and payment.status == "PENDING":
        # Conta pendente sem recebimento — permanece PENDING no financeiro.
        # O vencimento (se a prazo) já foi carimbado no lançamento, não aqui.
        return payment

    # R$ 0 sem parcela paga: não vira PAID (caso típico de retorno só com taxa isenta).
    if valor_total <= 0 and total_pago <= 0:
        payment.status = "PENDING"
        payment.amount = Decimal(0)
        payment.payment_date = None
        payment.save(update_fields=["status", "amount", "payment_date", "updated_at"])
        return payment

    if total_pago >= valor_total - Decimal("0.01"):
        payment.status = "PAID"
        payment.amount = max(total_pago, valor_total)
        payment.payment_date = ts
    elif total_pago > 0:
        payment.status = "PARTIAL"
        payment.amount = total_pago
        if not payment.payment_date:
            payment.payment_date = ts
    else:
        payment.status = "PENDING"
        payment.amount = Decimal(0)
        payment.payment_date = None

    payment.save(update_fields=["status", "amount", "payment_date", "updated_at"])

    # Ao quitar, limpa o vencimento (não é mais conta a receber a prazo).
    if payment.status == "PAID" and payment.data_vencimento:
        payment.data_vencimento = None
        payment.save(update_fields=["data_vencimento", "updated_at"])

    if payment.status in ("PAID", "PARTIAL"):
        _log_movimento_financeiro("Pagamento publicado", consulta, payment, usuario)
    if payment.status == "PAID":
        _agendar_nfse_pos_pagamento(consulta, payment)

    return payment
