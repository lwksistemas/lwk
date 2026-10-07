"""Relatório de repasse por consulta — cada atendimento com seus procedimentos.

Destinado ao profissional apresentar à clínica o que foi realizado e a comissão devida.
"""
from datetime import date
from decimal import Decimal

from django.utils import timezone

from .comissao_relatorio.finalizados import grupos_atendimentos_finalizados
from .comissao_relatorio_service import (
    _alocar_valores_pagamento,
    _calcular_comissao_regra,
    _combinar_formas_pagamento,
    _formatar_regra,
    _procedimentos_vinculados_consulta,
    _regras_profissional,
    _resolver_local_atendimento_efetivo,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
    _resolver_valor_consulta_cadastro,
)
from .convenio_service import resolver_convenio_atendimento_comissao


def _acumular_atendimento_prof(prof_map: dict, profissional, atendimento: dict) -> None:
    """Acumula dados de atendimento no agrupamento por profissional."""
    prof_id = profissional.id
    if prof_id not in prof_map:
        prof_map[prof_id] = {
            "professional_id": prof_id,
            "nome": profissional.nome,
            "atendimentos": [],
            "total_atendimentos": 0,
            "valor_consulta": Decimal(0),
            "valor_procedimento": Decimal(0),
            "valor_total": Decimal(0),
            "comissao_consulta": Decimal(0),
            "comissao_procedimento": Decimal(0),
            "comissao_total": Decimal(0),
        }
    entry = prof_map[prof_id]
    entry["atendimentos"].append(atendimento)
    entry["total_atendimentos"] += 1
    entry["valor_consulta"] += atendimento["valor_consulta"]
    entry["valor_procedimento"] += atendimento["valor_procedimentos"]
    entry["valor_total"] += atendimento["valor_consulta"] + atendimento["valor_procedimentos"]
    entry["comissao_consulta"] += atendimento["comissao_consulta"]
    entry["comissao_procedimento"] += atendimento["comissao_procedimentos"]
    entry["comissao_total"] += atendimento["comissao_atendimento"]


def _processar_grupo_repasse(grupo: dict, consulta, regras: dict, convenio_id) -> dict:
    """Processa um grupo de pagamento e retorna dict atendimento."""
    appt = grupo["appointment"]
    amount = grupo["total_amount"]
    payments = grupo.get("payments") or []
    procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
    valor_consulta_cad = _resolver_valor_consulta_cadastro(consulta, amount, procedimentos, regras)
    proc_com_regra = regras.get("procedimento_ids") or set()
    vc, vp_map = _alocar_valores_pagamento(amount, valor_consulta_cad, procedimentos, proc_com_regra)
    local_id, local_nome = _resolver_local_atendimento_efetivo(consulta, regras, valor_consulta_cad)
    regra_consulta = _resolver_regra_consulta(regras, local_id)
    modo_cc, regra_cc = _formatar_regra(regra_consulta)
    comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
    procs_linhas = []
    comissao_procedimentos = Decimal(0)
    valor_procedimentos = Decimal(0)
    for proc in procedimentos:
        proc_id = proc["procedure_id"]
        vp = vp_map.get(proc_id, Decimal(0))
        valor_procedimentos += vp
        regra_proc = _resolver_regra_procedimento(regras["procedimentos"], proc_id, convenio_id)
        com_proc = _calcular_comissao_regra(regra_proc, vp)
        modo_pc, regra_pc = _formatar_regra(regra_proc)
        comissao_procedimentos += com_proc
        procs_linhas.append({
            "procedure_id": proc_id, "nome": proc["procedimento_nome"],
            "valor": vp, "comissao": com_proc, "modo": modo_pc, "regra": regra_pc,
        })
    dt = appt.date
    if dt is not None and timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    data_str, hora_str = (dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")) if dt else ("—", "—")
    return {
        "appointment_id": appt.id,
        "data_atendimento": data_str, "hora_atendimento": hora_str,
        "paciente_nome": consulta.patient.nome if consulta.patient else (appt.patient.nome if appt.patient else "—"),
        "local_nome": local_nome or "—",
        "forma_pagamento": _combinar_formas_pagamento(payments),
        "valor_consulta": vc, "comissao_consulta": comissao_consulta,
        "modo_consulta": modo_cc, "regra_consulta": regra_cc,
        "procedimentos": procs_linhas, "valor_procedimentos": valor_procedimentos,
        "comissao_procedimentos": comissao_procedimentos,
        "valor_atendimento": vc + valor_procedimentos,
        "comissao_atendimento": comissao_consulta + comissao_procedimentos,
    }


def _manter_atendimentos_com_comissao(entry: dict) -> dict | None:
    """Tira atendimento sem comissão e recalcula o profissional. Sem resto, omite."""
    atendimentos = [a for a in entry["atendimentos"] if a["comissao_atendimento"] > 0]
    if not atendimentos:
        return None
    entry["atendimentos"] = atendimentos
    entry["total_atendimentos"] = len(atendimentos)
    entry["valor_consulta"] = sum((a["valor_consulta"] for a in atendimentos), Decimal(0))
    entry["valor_procedimento"] = sum((a["valor_procedimentos"] for a in atendimentos), Decimal(0))
    entry["valor_total"] = sum((a["valor_atendimento"] for a in atendimentos), Decimal(0))
    entry["comissao_consulta"] = sum((a["comissao_consulta"] for a in atendimentos), Decimal(0))
    entry["comissao_procedimento"] = sum((a["comissao_procedimentos"] for a in atendimentos), Decimal(0))
    entry["comissao_total"] = sum((a["comissao_atendimento"] for a in atendimentos), Decimal(0))
    return entry


def _calcular_totais_repasse(profissionais: list) -> dict:
    """Suma totais globais a partir da lista de profissionais."""
    return {
        "total_atendimentos": sum(p["total_atendimentos"] for p in profissionais),
        "valor_consulta": sum(p["valor_consulta"] for p in profissionais),
        "valor_procedimento": sum(p["valor_procedimento"] for p in profissionais),
        "valor_total": sum(p["valor_total"] for p in profissionais),
        "comissao_consulta": sum(p["comissao_consulta"] for p in profissionais),
        "comissao_procedimento": sum(p["comissao_procedimento"] for p in profissionais),
        "comissao_total": sum(p["comissao_total"] for p in profissionais),
    }


def calcular_repasse_por_consulta(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
) -> dict:
    grupos, consulta_map = grupos_atendimentos_finalizados(
        data_inicio=data_inicio,
        data_fim=data_fim,
        professional_id=professional_id,
    )

    prof_map: dict[int, dict] = {}
    regras_cache: dict[int, dict] = {}

    for grupo in grupos:
        appt = grupo["appointment"]
        profissional = grupo.get("profissional") or appt.professional
        if not appt or not profissional:
            continue
        consulta = consulta_map.get(appt.id)
        if not consulta:
            continue
        procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
        if not procedimentos and grupo["total_amount"] <= 0:
            continue
        prof_id = profissional.id
        if prof_id not in regras_cache:
            regras_cache[prof_id] = _regras_profissional(prof_id)
        regras = regras_cache[prof_id]
        convenio_id = resolver_convenio_atendimento_comissao(appt, consulta, procedimentos)
        atendimento = _processar_grupo_repasse(grupo, consulta, regras, convenio_id)
        _acumular_atendimento_prof(prof_map, profissional, atendimento)

    profissionais = []
    for entry in prof_map.values():
        filtrado = _manter_atendimentos_com_comissao(entry)
        if filtrado is not None:
            profissionais.append(filtrado)
    profissionais.sort(key=lambda p: p["nome"])
    return {"profissionais": profissionais, "totais": _calcular_totais_repasse(profissionais)}
