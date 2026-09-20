"""Cálculo do vencimento de pagamentos a prazo a partir da política do paciente.

A política é configurada pelo administrador no prontuário do paciente:
- DIAS_APOS: vence em (data de finalização + N dias).
- DIA_FIXO: vence no dia X do MÊS SEGUINTE à finalização.

Se o paciente não tem política válida, receber "a prazo" é bloqueado
(ver PrazoNaoConfiguradoError), evitando conta a receber sem vencimento.
"""
from __future__ import annotations

import calendar
from datetime import date

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
        from datetime import timedelta

        return data_finalizacao + timedelta(days=int(dias))

    if modo == Patient.PRAZO_MODO_DIA_FIXO:
        dia = patient.prazo_pagamento_dia_mes
        if not dia or dia < 1:
            raise PrazoNaoConfiguradoError()
        return _proximo_dia_fixo(data_finalizacao, int(dia))

    raise PrazoNaoConfiguradoError()
