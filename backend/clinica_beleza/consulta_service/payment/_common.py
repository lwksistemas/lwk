from decimal import Decimal
from functools import wraps

from core.decimal_utils import to_decimal

from .._deps import logger

_METODOS_VALIDOS = frozenset({"CASH", "CREDIT_CARD", "DEBIT_CARD", "PIX", "TRANSFER", "PRAZO", "DESPESA"})
_METODO_PRAZO = "PRAZO"


def _tenant_atomic(func):
    """@atomic no alias do tenant — select_for_update falha se o atomic for só no default."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        from clinica_beleza.estoque_service import tenant_atomic

        with tenant_atomic():
            return func(*args, **kwargs)

    return wrapper


def _tem_entrada_prazo(lista) -> bool:
    """True se alguma entrada usa a forma 'a prazo'."""
    return bool(lista) and any(e.get("payment_method") == _METODO_PRAZO for e in lista)


def _validar_prazo_paciente_para_entradas(consulta, lista) -> None:
    """Bloqueia recebimento a prazo quando o paciente não tem política configurada.

    Feedback imediato à recepção no 'Receber pagamento' — evita conta a receber
    sem vencimento. A configuração é feita só pelo admin no prontuário.
    """
    if not _tem_entrada_prazo(lista):
        return
    from ...prazo_service import PrazoNaoConfiguradoError

    patient = getattr(getattr(consulta, "appointment", None), "patient", None) or getattr(consulta, "patient", None)
    if patient is None or not getattr(patient, "tem_prazo_pagamento", False):
        raise PrazoNaoConfiguradoError()


def _calcular_vencimento_prazo(payment, data_base):
    """Calcula a data de vencimento conforme a política do paciente do payment.

    Retorna date ou None (se não é a prazo, sem paciente, ou sem política).
    A base é a data do lançamento a prazo (não a finalização da consulta).
    """
    if payment.payment_method != _METODO_PRAZO:
        return None
    appointment = getattr(payment, "appointment", None)
    patient = getattr(appointment, "patient", None)
    if patient is None:
        return None
    from ...prazo_service import PrazoNaoConfiguradoError, calcular_vencimento

    try:
        return calcular_vencimento(patient, data_base)
    except PrazoNaoConfiguradoError:
        logger.warning("Payment %s a prazo sem política de prazo do paciente", getattr(payment, "pk", None))
        return None


def _tentar_nfse_pos_pagamento(consulta, payment):
    """Dispara emissão NFS-e após pagamento confirmado (não bloqueia fluxo)."""
    try:
        from ...nfse_consulta_service import tentar_emitir_nfse_consulta

        tentar_emitir_nfse_consulta(consulta, payment)
    except Exception:
        logger.exception("Erro ao tentar NFS-e após pagamento (consulta %s)", consulta.id)


def _calcular_valor_total_com_desconto(valor_bruto: Decimal, desconto, payment) -> Decimal:
    """Calcula valor_total após desconto, preservando desconto anterior se nenhum novo informado."""
    valor_desconto = to_decimal(desconto, "desconto") if desconto not in (None, "") else Decimal(0)
    if valor_desconto is None:
        valor_desconto = Decimal(0)
    if valor_desconto < 0:
        raise ValueError("Desconto não pode ser negativo.")
    if valor_desconto > valor_bruto:
        raise ValueError("Desconto não pode ser maior que o total do atendimento.")
    valor_total = max(valor_bruto - valor_desconto, Decimal(0))
    if payment and valor_desconto == 0 and payment.valor_total is not None and payment.valor_total < valor_bruto:
        try:
            ja_pago = payment.valor_pago_parcelas
        except Exception:
            ja_pago = Decimal(0)
        if ja_pago > 0:
            valor_total = payment.valor_total
    return valor_total


def _garantir_ou_criar_payment(consulta_service, appointment, valor_total, metodo_principal, comissao_pct, comissao_val, valor_desconto, payment):
    """Cria ou atualiza o objeto Payment. Retorna o payment (novo ou atualizado)."""
    if not payment:
        return consulta_service.Payment.objects.create(
            appointment=appointment,
            amount=Decimal(0),
            valor_total=valor_total,
            payment_method=metodo_principal,
            status="PENDING",
            comissao_percentual=comissao_pct,
            comissao_valor=comissao_val,
            loja_id=appointment.loja_id,
            desconto=valor_desconto if valor_desconto > 0 else Decimal(0),
            notes=f"Desconto: R$ {valor_desconto}" if valor_desconto > 0 else None,
        )
    payment.valor_total = valor_total
    payment.payment_method = metodo_principal
    payment.comissao_percentual = comissao_pct
    payment.comissao_valor = comissao_val
    if valor_desconto > 0:
        payment.desconto = valor_desconto
        payment.notes = f"Desconto: R$ {valor_desconto}"
    return payment


def _finalizar_payment_draft(payment, valor_total, lista, valor_desconto, mark_as_paid, ts):
    """Cria parcelas, recalcula saldo e salva payment como DRAFT.

    Entradas a prazo não geram parcela paga: o valor fica em aberto no Financeiro
    para o cliente quitar depois.
    """
    from ...models.financeiro import PaymentParcela
    so_prazo = bool(lista) and all(e["payment_method"] == _METODO_PRAZO for e in lista)
    for entrada in lista:
        if entrada["payment_method"] == _METODO_PRAZO:
            continue
        PaymentParcela.objects.create(
            payment=payment,
            valor=entrada["valor"],
            payment_method=entrada["payment_method"],
            payment_date=ts.date(),
            loja_id=payment.loja_id,
        )
    venc_prazo = None
    if so_prazo:
        payment.payment_method = _METODO_PRAZO
        notes = (payment.notes or "").strip()
        if "A prazo" not in notes:
            payment.notes = f"{notes} | A prazo — cliente paga depois".strip(" |")
        # Carimba o vencimento no momento do lançamento a prazo (não na finalização).
        venc_prazo = _calcular_vencimento_prazo(payment, ts.date())
        payment.data_vencimento = venc_prazo
    total_pago = payment.valor_pago_parcelas
    try:
        saldo_apos = payment.saldo_devedor
    except (TypeError, ArithmeticError) as exc:
        logger.warning("Erro saldo_devedor payment %s: %s", payment.pk, exc)
        saldo_apos = max(valor_total - total_pago, Decimal(0))
    quitou = total_pago >= valor_total or (mark_as_paid and saldo_apos <= Decimal("0.01"))
    payment.payment_date = None
    if so_prazo and total_pago <= Decimal("0.01"):
        payment.status = "PENDING"
        payment.amount = Decimal(0)
    else:
        payment.status = "DRAFT"
        payment.amount = max(total_pago, valor_total) if quitou else total_pago
    update_fields = ["amount", "valor_total", "payment_method", "status", "payment_date", "comissao_percentual", "comissao_valor", "updated_at"]
    if valor_desconto > 0:
        payment.desconto = valor_desconto
        update_fields.append("desconto")
    if valor_desconto > 0 or so_prazo:
        update_fields.append("notes")
    if so_prazo:
        update_fields.append("data_vencimento")
    payment.save(update_fields=update_fields)


def _normalize_entradas(entradas, *, payment_method="CASH", amount=None):
    """Normaliza lista de entradas [{payment_method, valor}, ...].
    Sem entradas: usa payment_method + amount (path legado).
    """
    if entradas is None:
        if amount is None:
            return None  # caller usa valor total
        valor = to_decimal(amount, "amount")
        if valor is None or valor <= 0:
            raise ValueError("Valor deve ser maior que zero.")
        metodo = (payment_method or "CASH").strip().upper() or "CASH"
        if metodo not in _METODOS_VALIDOS:
            raise ValueError("Forma de pagamento inválida.")
        return [{"payment_method": metodo, "valor": valor}]

    if not isinstance(entradas, (list, tuple)) or len(entradas) == 0:
        raise ValueError("Informe ao menos uma forma de pagamento.")

    normalizadas = []
    for i, item in enumerate(entradas):
        if not isinstance(item, dict):
            raise ValueError(f"Entrada {i + 1} inválida.")
        metodo = (item.get("payment_method") or "CASH").strip().upper() or "CASH"
        if metodo not in _METODOS_VALIDOS:
            raise ValueError(f"Forma de pagamento inválida na entrada {i + 1}.")
        valor = to_decimal(item.get("valor"), f"valor da entrada {i + 1}")
        if valor is None or valor <= 0:
            raise ValueError(f"Valor da entrada {i + 1} deve ser maior que zero.")
        normalizadas.append({"payment_method": metodo, "valor": valor})
    return normalizadas
