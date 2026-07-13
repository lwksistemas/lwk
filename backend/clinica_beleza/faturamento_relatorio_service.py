"""Service para relatório de faturamento — Clínica da Beleza.

Agrupa receita por profissional, procedimento, local de atendimento ou convênio.
Baseado em Payment (status=PAID) como fonte de verdade — espelha o padrão
de comissao_relatorio_service.py para consistência.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Literal

from .models import Consulta, Payment

AgrupamentoType = Literal["profissional", "procedimento", "local", "convenio"]


def calcular_faturamento(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    agrupar: AgrupamentoType = "profissional",
    professional_id: int | None = None,
) -> dict:
    """Calcula faturamento da clínica agrupado pelo critério selecionado.

    Fonte: Payment.status='PAID' com payment_date no período.
    Valores: taxa de consulta (via Consulta.valor_consulta) + procedimentos
    (via AppointmentProcedure.valor).

    Retorna dict com 'linhas' (lista) e 'totais'.
    """
    # Filtrar pagamentos pagos no período (mesmo padrão do relatório de comissões)
    qs = Payment.objects.filter(status="PAID").select_related(
        "appointment__professional",
        "appointment__patient",
        "appointment__procedure",
        "appointment__convenio",
        "appointment__local_atendimento",
    )

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    # Carregar consultas vinculadas para ter valor_consulta e local
    payments_list = list(qs.prefetch_related("appointment__appointment_procedures__procedure"))
    appt_ids = [p.appointment_id for p in payments_list if p.appointment_id]
    consulta_map = {}
    if appt_ids:
        for c in Consulta.objects.filter(
            appointment_id__in=appt_ids,
        ).select_related("local_atendimento", "procedure", "convenio"):
            consulta_map[c.appointment_id] = c

    # Acumular dados por grupo
    grupos: dict[str, dict] = defaultdict(lambda: {
        "nome": "",
        "total_atendimentos": 0,
        "valor_consulta": Decimal(0),
        "valor_procedimento": Decimal(0),
        "valor_total": Decimal(0),
    })

    for payment in payments_list:
        appt = payment.appointment
        if not appt:
            continue

        consulta = consulta_map.get(appt.id)

        # Determinar chave e nome do grupo
        chave = _get_grupo_chave(appt, consulta, agrupar)
        nome = _get_grupo_nome(appt, consulta, agrupar)

        grupo = grupos[chave]
        grupo["nome"] = nome
        grupo["total_atendimentos"] += 1

        # Valor da taxa de consulta (do registro Consulta ou local)
        valor_consulta = Decimal(0)
        if consulta:
            vc = Decimal(str(consulta.valor_consulta or 0))
            if vc > 0:
                valor_consulta = vc
            elif consulta.local_atendimento:
                valor_consulta = Decimal(str(consulta.local_atendimento.valor_consulta or 0))

        # Valor dos procedimentos (AppointmentProcedure.valor ou procedure.preco)
        valor_proc = Decimal(0)
        for ap in appt.appointment_procedures.all():
            valor_proc += ap.valor or ap.procedure.preco or Decimal(0)

        # Se não tem procedimentos nem consulta com valor, usar amount total
        if valor_consulta == 0 and valor_proc == 0:
            grupo["valor_total"] += payment.amount or Decimal(0)
        else:
            grupo["valor_consulta"] += valor_consulta
            grupo["valor_procedimento"] += valor_proc
            grupo["valor_total"] += valor_consulta + valor_proc

    # Converter para lista ordenada por valor total desc
    linhas = sorted(grupos.values(), key=lambda x: x["valor_total"], reverse=True)

    # Serializar Decimal para float
    for linha in linhas:
        linha["valor_consulta"] = float(linha["valor_consulta"])
        linha["valor_procedimento"] = float(linha["valor_procedimento"])
        linha["valor_total"] = float(linha["valor_total"])

    totais = {
        "total_atendimentos": sum(linha["total_atendimentos"] for linha in linhas),
        "valor_consulta": sum(linha["valor_consulta"] for linha in linhas),
        "valor_procedimento": sum(linha["valor_procedimento"] for linha in linhas),
        "valor_total": sum(linha["valor_total"] for linha in linhas),
    }

    return {
        "linhas": linhas,
        "totais": totais,
        "agrupamento": agrupar,
    }


def _get_grupo_chave(appt, consulta, agrupar: AgrupamentoType) -> str:
    """Retorna chave única para agrupamento."""
    if agrupar == "profissional":
        return f"prof_{appt.professional_id or 0}"
    if agrupar == "procedimento":
        # Primeiro procedimento do AppointmentProcedure
        aps = list(appt.appointment_procedures.all())
        if aps:
            return f"proc_{aps[0].procedure_id}"
        if appt.procedure_id:
            return f"proc_{appt.procedure_id}"
        return "proc_consulta"
    if agrupar == "local":
        local = None
        if consulta:
            local = consulta.local_atendimento
        if not local:
            local = appt.local_atendimento
        return f"local_{local.id if local else 0}"
    if agrupar == "convenio":
        conv_id = appt.convenio_id or 0
        return f"conv_{conv_id}"
    return "outros"


def _get_grupo_nome(appt, consulta, agrupar: AgrupamentoType) -> str:
    """Retorna nome legível para o grupo."""
    if agrupar == "profissional":
        prof = appt.professional
        return getattr(prof, "nome", "") or "Sem profissional"
    if agrupar == "procedimento":
        aps = list(appt.appointment_procedures.all())
        if aps:
            return aps[0].procedure.nome
        if appt.procedure_id and appt.procedure:
            return appt.procedure.nome
        return "Consulta"
    if agrupar == "local":
        local = None
        if consulta:
            local = consulta.local_atendimento
        if not local:
            local = appt.local_atendimento
        if local:
            return getattr(local, "nome", "") or "Local sem nome"
        return "Sem local definido"
    if agrupar == "convenio":
        convenio = appt.convenio
        if convenio:
            return convenio.nome
        return "Particular"
    return "Outros"
