"""Lançamento e saldo de procedimentos feitos antes do sistema."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from .models.financeiro import ProcedimentoAnteriorRecebimento

FORMAS_RECEBIMENTO = dict(ProcedimentoAnteriorRecebimento.FORMAS)
CENTAVOS = Decimal("0.01")


def _dinheiro(valor, nome: str) -> Decimal:
    try:
        quantia = Decimal(str(valor if valor not in (None, "") else 0))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Informe um {nome} válido.") from exc
    return quantia.quantize(CENTAVOS)


def vencimento_da_diferenca(patient, data_lancamento: date) -> date:
    """A diferença vence pela regra de venda a prazo já configurada na cliente."""
    from .prazo_service import PrazoNaoConfiguradoError, calcular_vencimento

    if patient is None or not getattr(patient, "tem_prazo_pagamento", False):
        raise ValueError(
            "A diferença precisa do prazo desta cliente. "
            "Configure como ela paga a prazo antes de lançar."
        )
    try:
        return calcular_vencimento(patient, data_lancamento)
    except PrazoNaoConfiguradoError as exc:
        raise ValueError(str(exc)) from exc


def validar_lancamento_anterior(
    data_procedimento: date | None,
    nome: str,
    valor,
    valor_pago,
    hoje: date,
    data_pagamento: date | None = None,
    patient=None,
) -> tuple[str, Decimal, Decimal, date | None, date | None]:
    """Confere o procedimento, o que já foi pago e o vencimento da diferença.

    Returns:
        nome, valor, valor_pago, data_pagamento, data_vencimento.
        data_vencimento só existe quando ainda falta receber.
    """
    titulo = (nome or "").strip()
    if not titulo:
        raise ValueError("Informe o nome do procedimento.")
    if len(titulo) > 200:
        raise ValueError("O nome do procedimento pode ter no máximo 200 caracteres.")
    if data_procedimento is None:
        raise ValueError("Informe a data em que o procedimento foi feito.")
    if data_procedimento > hoje:
        raise ValueError("A data do procedimento não pode ser futura.")
    total = _dinheiro(valor, "valor")
    pago = _dinheiro(valor_pago, "valor já pago")
    if total <= 0:
        raise ValueError("O valor do procedimento precisa ser maior que zero.")
    if pago < 0:
        raise ValueError("O valor já pago não pode ser negativo.")
    if pago > total:
        raise ValueError("O valor já pago não pode ser maior que o valor do procedimento.")
    if pago > 0:
        if data_pagamento is None:
            raise ValueError("Informe a data do pagamento.")
        if data_pagamento > hoje:
            raise ValueError("A data do pagamento não pode ser futura.")
        if data_pagamento < data_procedimento:
            raise ValueError("A data do pagamento não pode ser anterior ao procedimento.")
    else:
        data_pagamento = None
    vencimento = vencimento_da_diferenca(patient, hoje) if pago < total else None
    return titulo, total, pago, data_pagamento, vencimento


def saldo_anterior(valor, valor_pago, recebimentos) -> Decimal:
    """Saldo = valor do procedimento − entrada já paga − recebimentos lançados aqui."""
    total = _dinheiro(valor, "valor")
    pago = _dinheiro(valor_pago, "valor já pago")
    for item in recebimentos:
        pago += _dinheiro(item, "recebimento")
    saldo = (total - pago).quantize(CENTAVOS)
    return saldo if saldo > 0 else Decimal("0.00")


def validar_recebimento(saldo, valor, data_recebimento: date | None, hoje: date, data_procedimento: date | None, forma: str):
    """Confere uma baixa do saldo. Devolve (valor, forma)."""
    if data_recebimento is None:
        raise ValueError("Informe a data do recebimento.")
    if data_recebimento > hoje:
        raise ValueError("A data do recebimento não pode ser futura.")
    if data_procedimento is not None and data_recebimento < data_procedimento:
        raise ValueError("A data do recebimento não pode ser anterior ao procedimento.")
    quantia = _dinheiro(valor, "valor recebido")
    if quantia <= 0:
        raise ValueError("Informe o valor recebido.")
    aberto = _dinheiro(saldo, "saldo")
    if aberto <= 0:
        raise ValueError("Este procedimento não tem saldo para receber.")
    if quantia > aberto:
        raise ValueError("O valor recebido não pode ser maior que o saldo.")
    codigo = (forma or "").strip()
    if codigo not in FORMAS_RECEBIMENTO:
        raise ValueError("Escolha a forma de pagamento.")
    return quantia, codigo
