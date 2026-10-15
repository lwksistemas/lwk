"""Cálculo do vencimento de pagamentos a prazo a partir da política do paciente.

A política é configurada pelo administrador no prontuário do paciente:
- DIAS_APOS: vence em (data de finalização + N dias).
- DIA_FIXO: vence no dia X do mês (neste mês, se o dia ainda não passou).
- SEMANAL: vence 7 dias depois de finalizar a consulta.

Se o paciente não tem política válida, receber "a prazo" é bloqueado
(ver PrazoNaoConfiguradoError), evitando conta a receber sem vencimento.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from .models.patients import Patient

MSG_PRAZO_NAO_CONFIGURADO = (
    "Este paciente não tem prazo de pagamento configurado. "
    "Peça ao administrador para configurar no prontuário."
)


class PrazoNaoConfiguradoError(ValueError):
    """Paciente sem política de prazo válida — não pode receber a prazo."""

    def __init__(self, mensagem: str = MSG_PRAZO_NAO_CONFIGURADO):
        super().__init__(mensagem)


def _proximo_dia_fixo(referencia: date, dia: int) -> date:
    """Retorna o próximo 'dia X' a partir de `referencia` (inclusive).

    Se ainda não passou o dia X no mês corrente, vence neste mês;
    se já passou (ou é depois), vence no mês seguinte.
    Ex.: dia fixo 10 — lançou 05/10 → 10/10; lançou 15/10 → 10/11; lançou 10/10 → 10/10.

    `dia` é 1..28 na configuração; clampa por segurança contra o último dia do mês.
    """
    if dia >= referencia.day:
        ano, mes = referencia.year, referencia.month
    else:
        ano = referencia.year + (1 if referencia.month == 12 else 0)
        mes = 1 if referencia.month == 12 else referencia.month + 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo_dia))


def validar_regra_prazo(modo: str, dias, dia_mes) -> tuple[str, int | None, int | None]:
    """Confere a regra de um prazo criado pelo administrador.

    Returns:
        (modo, dias, dia_mes) com o campo que não se aplica zerado.

    Raises:
        ValueError: regra incompleta ou modo desconhecido.
    """
    modo = (modo or "").strip()
    if modo == Patient.PRAZO_MODO_DIAS_APOS:
        try:
            quantidade = int(dias)
        except (TypeError, ValueError):
            quantidade = 0
        if quantidade < 1 or quantidade > 365:
            raise ValueError("Informe de 1 a 365 dias para pagar.")
        return modo, quantidade, None
    if modo == Patient.PRAZO_MODO_DIA_FIXO:
        try:
            dia = int(dia_mes)
        except (TypeError, ValueError):
            dia = 0
        if dia < 1 or dia > 28:
            raise ValueError("Informe o dia do mês de 1 a 28.")
        return modo, None, dia
    if modo == Patient.PRAZO_MODO_SEMANAL:
        return modo, None, None
    raise ValueError("Escolha dias após finalizar a consulta, um dia fixo do mês ou semanal.")


def aplicar_prazo_escolhido(patient: Patient, opcao) -> Patient:
    """Copia a regra do prazo criado pelo admin para a cliente. opcao=None tira o prazo."""
    if opcao is None:
        patient.prazo_opcao_id = None
        patient.prazo_pagamento_modo = Patient.PRAZO_MODO_SEM
        patient.prazo_pagamento_dias = None
        patient.prazo_pagamento_dia_mes = None
        return patient
    patient.prazo_opcao_id = opcao.pk
    patient.prazo_pagamento_modo = opcao.modo
    if opcao.modo == Patient.PRAZO_MODO_DIAS_APOS:
        patient.prazo_pagamento_dias = opcao.dias
        patient.prazo_pagamento_dia_mes = None
    elif opcao.modo == Patient.PRAZO_MODO_DIA_FIXO:
        patient.prazo_pagamento_dia_mes = opcao.dia_mes
        patient.prazo_pagamento_dias = None
    elif opcao.modo == Patient.PRAZO_MODO_SEMANAL:
        patient.prazo_pagamento_dias = None
        patient.prazo_pagamento_dia_mes = None
    else:
        raise ValueError("Este prazo não tem regra de vencimento.")
    return patient


def calcular_vencimento(patient: Patient, data_finalizacao: date) -> date:
    """Calcula o vencimento conforme a política de prazo do paciente.

    Args:
        patient: paciente com a política configurada.
        data_finalizacao: data em que a consulta foi finalizada (base do cálculo).

    Returns:
        date do vencimento.

    Raises:
        PrazoNaoConfiguradoError: se o paciente não tem política válida.

    """
    modo = getattr(patient, "prazo_pagamento_modo", "") or ""

    if modo == Patient.PRAZO_MODO_DIAS_APOS:
        dias = patient.prazo_pagamento_dias
        if not dias or dias < 1:
            raise PrazoNaoConfiguradoError()
        return data_finalizacao + timedelta(days=int(dias))

    if modo == Patient.PRAZO_MODO_DIA_FIXO:
        dia = patient.prazo_pagamento_dia_mes
        if not dia or dia < 1:
            raise PrazoNaoConfiguradoError()
        return _proximo_dia_fixo(data_finalizacao, int(dia))

    if modo == Patient.PRAZO_MODO_SEMANAL:
        return data_finalizacao + timedelta(days=7)

    raise PrazoNaoConfiguradoError()
