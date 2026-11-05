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


def status_financeiro_anterior(valor, valor_pago, saldo) -> str:
    """Pendente sem entrada, parcial se já entrou dinheiro e ainda falta, pago se zerou."""
    aberto = _dinheiro(saldo, "saldo")
    if aberto <= 0:
        return "PAID"
    total = _dinheiro(valor, "valor")
    entrada = _dinheiro(valor_pago, "valor já pago")
    if entrada > 0 or (total - aberto - entrada) > 0:
        return "PARTIAL"
    return "PENDING"


def linha_financeiro_anterior(item, recebimentos, hoje: date) -> dict:
    """Linha da página do financeiro. Não é pagamento de consulta e não gera comissão."""
    valores = []
    datas = []
    for recebimento in recebimentos:
        valores.append(getattr(recebimento, "valor", recebimento))
        data_item = getattr(recebimento, "data", None)
        if data_item is not None:
            datas.append(data_item)
    saldo = saldo_anterior(item.valor, item.valor_pago, valores)
    status = status_financeiro_anterior(item.valor, item.valor_pago, saldo)
    pago = (_dinheiro(item.valor, "valor") - saldo).quantize(CENTAVOS)
    vencimento = getattr(item, "data_vencimento", None)
    vencido = bool(vencimento and saldo > 0 and vencimento < hoje)
    ultima = max(datas) if datas else getattr(item, "data_pagamento", None)
    paciente = getattr(item, "patient", None)
    return {
        "id": item.id,
        "origem": "procedimento_anterior",
        "patient_id": getattr(item, "patient_id", None) or getattr(paciente, "id", None),
        "appointment": None,
        "amount": str(pago if status != "PENDING" else Decimal("0.00")),
        "valor_total": str(item.valor),
        "valor_total_efetivo": float(item.valor),
        "saldo_devedor": float(saldo),
        "payment_method": "PRAZO" if saldo > 0 else "",
        "status": status,
        "payment_date": ultima.isoformat() if ultima and status != "PENDING" else None,
        "data_vencimento": vencimento.isoformat() if vencimento else None,
        "vencido": vencido,
        "dias_atraso": (hoje - vencimento).days if vencido else 0,
        "retorno_gratuito": False,
        "consulta_id": None,
        "comissao_percentual": 0,
        "comissao_valor": "0.00",
        "desconto": "0.00",
        "paciente_nome": getattr(paciente, "nome", "") or "",
        "paciente_tem_prazo": True,
        "profissional_nome": "",
        "operador_nome": "",
        "procedimento_nome": item.nome,
        "data_atendimento": item.data_procedimento.isoformat(),
        "created_at": item.created_at.isoformat() if getattr(item, "created_at", None) else "",
        "datas_recebimento": [dia.isoformat() for dia in datas],
    }


def entra_na_lista_do_financeiro(linha, *, status=None, date_filter=None, professional_id=None) -> bool:
    """Saldo em aberto continua na lista para receber, mesmo com filtro de um dia."""
    if professional_id not in (None, ""):
        return False
    if status == "CANCELLED":
        return False
    if status and linha["status"] != status:
        return False
    if not date_filter or linha["status"] in ("PENDING", "PARTIAL"):
        return True
    dia = str(date_filter)[:10]
    datas = {
        str(linha.get("data_atendimento") or "")[:10],
        str(linha.get("payment_date") or "")[:10],
        *[str(item)[:10] for item in linha.get("datas_recebimento") or []],
    }
    return dia in datas


def linhas_financeiras_anteriores(*, status=None, date_filter=None, professional_id=None, hoje: date | None = None) -> list[dict]:
    """Procedimentos anteriores com saldo, no formato da lista de receitas."""
    from django.utils import timezone

    from .models import ProcedimentoAnterior

    if professional_id not in (None, ""):
        return []
    hoje = hoje or timezone.localdate()
    linhas = []
    itens = (
        ProcedimentoAnterior.objects
        .select_related("patient")
        .prefetch_related("recebimentos")
        .order_by("data_vencimento", "-id")
    )
    for item in itens:
        linha = linha_financeiro_anterior(item, list(item.recebimentos.all()), hoje)
        if entra_na_lista_do_financeiro(
            linha, status=status, date_filter=date_filter, professional_id=professional_id,
        ):
            linha.pop("datas_recebimento", None)
            linhas.append(linha)
    return linhas


def somar_saldo_procedimentos_anteriores() -> float:
    """Saldo ainda aberto desses lançamentos, para o cartão A receber."""
    from .models import ProcedimentoAnterior

    total = Decimal("0.00")
    itens = ProcedimentoAnterior.objects.prefetch_related("recebimentos")
    for item in itens:
        total += saldo_anterior(item.valor, item.valor_pago, [r.valor for r in item.recebimentos.all()])
    return float(total)
