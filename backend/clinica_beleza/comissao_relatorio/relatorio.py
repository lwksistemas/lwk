from datetime import date
from decimal import Decimal

from ..convenio_service import resolver_convenio_atendimento_comissao
from ..models import Payment
from .alocacao import _alocar_valores_pagamento
from .constants import CHAVE_CONSULTA, LABEL_CONSULTA
from .formatting import _combinar_formas_pagamento, _formatar_regra
from .local_consulta import _resolver_local_atendimento_efetivo, _resolver_valor_consulta_cadastro
from .pagamentos import _agrupar_pagamentos_por_agendamento, _obter_ou_criar_detalhe
from .procedimentos import _procedimentos_vinculados_consulta
from .regras import (
    _calcular_comissao_regra,
    _regras_profissional,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
    _rotulo_convenio_comissao,
)


def calcular_comissoes(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
) -> dict:
    """Calcula comissões dos profissionais.
    Apenas pagamentos com consulta vinculada; cada procedimento do agendamento
    gera linha de detalhe associada à consulta (local + taxa de consulta).
    """
    qs = Payment.objects.filter(status="PAID").select_related(
        "appointment__professional",
        "appointment__procedure",
        "appointment__patient",
        "appointment__convenio",
    )

    if data_inicio:
        qs = qs.filter(payment_date__date__gte=data_inicio)
    if data_fim:
        qs = qs.filter(payment_date__date__lte=data_fim)
    if professional_id:
        qs = qs.filter(appointment__professional_id=professional_id)

    from ..models import Consulta

    consulta_map = {}
    consulta_ids = qs.values_list("appointment_id", flat=True)
    consultas = Consulta.objects.filter(
        appointment_id__in=consulta_ids,
    ).select_related("local_atendimento", "procedure", "convenio")
    for c in consultas:
        consulta_map[c.appointment_id] = c

    prof_data = {}
    regras_cache = {}

    payments_list = list(qs.prefetch_related("appointment__appointment_procedures__procedure"))
    for grupo in _agrupar_pagamentos_por_agendamento(payments_list):
        appt = grupo["appointment"]
        if not appt or not appt.professional:
            continue

        consulta = consulta_map.get(appt.id)
        if not consulta:
            continue

        procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
        if not procedimentos:
            continue

        prof_id = appt.professional_id
        prof_nome = appt.professional.nome

        amount = grupo["total_amount"]

        if prof_id not in regras_cache:
            regras_cache[prof_id] = _regras_profissional(prof_id)
        regras = regras_cache[prof_id]

        valor_consulta_cad = _resolver_valor_consulta_cadastro(consulta, amount, procedimentos, regras)
        proc_com_regra = regras.get("procedimento_ids") or set()
        convenio_id = resolver_convenio_atendimento_comissao(appt, consulta, procedimentos)
        vc, vp_map = _alocar_valores_pagamento(
            amount, valor_consulta_cad, procedimentos, proc_com_regra,
        )
        local_id, local_nome = _resolver_local_atendimento_efetivo(
            consulta, regras, valor_consulta_cad,
        )
        regra_consulta = _resolver_regra_consulta(regras, local_id)
        forma_pagamento = _combinar_formas_pagamento(grupo["payments"])

        comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
        comissao_procedimentos = Decimal(0)
        for proc in procedimentos:
            vp = vp_map.get(proc["procedure_id"], Decimal(0))
            regra_proc = _resolver_regra_procedimento(
                regras["procedimentos"], proc["procedure_id"], convenio_id,
            )
            comissao_procedimentos += _calcular_comissao_regra(regra_proc, vp)

        comissao_total = comissao_consulta + comissao_procedimentos

        if prof_id not in prof_data:
            prof_data[prof_id] = {
                "professional_id": prof_id,
                "nome": prof_nome,
                "total_atendimentos": 0,
                "valor_consulta": Decimal(0),
                "valor_procedimento": Decimal(0),
                "valor_total": Decimal(0),
                "comissao_consulta": Decimal(0),
                "comissao_procedimento": Decimal(0),
                "comissao_total": Decimal(0),
                "comissao_consulta_regra": None,
                "comissao_consulta_regras_por_local": [],
                "detalhes": [],
            }

        entry = prof_data[prof_id]
        entry["total_atendimentos"] += 1
        entry["valor_consulta"] += vc
        entry["valor_procedimento"] += sum(vp_map.values())
        entry["valor_total"] += amount
        entry["comissao_consulta"] += comissao_consulta
        entry["comissao_procedimento"] += comissao_procedimentos
        entry["comissao_total"] += comissao_total

        modo_cc, regra_cc = _formatar_regra(regra_consulta)
        if vc > 0 or comissao_consulta > 0 or regra_consulta or local_id:
            chave_consulta = f"{local_nome}||{CHAVE_CONSULTA}"
            det_consulta = _obter_ou_criar_detalhe(entry, chave_consulta, {
                "tipo_linha": "consulta",
                "local_nome": local_nome,
                "forma_pagamento": forma_pagamento,
                "procedimento_nome": LABEL_CONSULTA,
                "procedimento_id": None,
                "vinculado_consulta": True,
                "qtd": 0,
                "valor_consulta": Decimal(0),
                "valor_procedimento": Decimal(0),
                "valor_total": Decimal(0),
                "comissao_consulta": Decimal(0),
                "comissao_procedimento": Decimal(0),
                "comissao": Decimal(0),
                "modo_consulta": modo_cc,
                "regra_consulta": regra_cc,
                "modo_procedimento": "",
                "regra_procedimento": "",
            })
            det_consulta["qtd"] += 1
            det_consulta["valor_consulta"] += vc
            det_consulta["valor_total"] += vc
            det_consulta["comissao_consulta"] += comissao_consulta
            det_consulta["comissao"] += comissao_consulta
            if forma_pagamento and forma_pagamento != "—":
                pagamentos_atuais = [
                    p.strip() for p in (det_consulta.get("forma_pagamento") or "").split(" + ")
                    if p.strip() and p.strip() != "—"
                ]
                for label in forma_pagamento.split(" + "):
                    if label and label not in pagamentos_atuais:
                        pagamentos_atuais.append(label)
                det_consulta["forma_pagamento"] = " + ".join(pagamentos_atuais) if pagamentos_atuais else forma_pagamento

        for proc in procedimentos:
            proc_id = proc["procedure_id"]
            vp = vp_map.get(proc_id, Decimal(0))
            regra_proc = _resolver_regra_procedimento(
                regras["procedimentos"], proc_id, convenio_id,
            )
            com_proc = _calcular_comissao_regra(regra_proc, vp)
            modo_pc, regra_pc = _formatar_regra(regra_proc)

            chave_proc = (
                f"proc:{proc_id}:{convenio_id or 0}:{regra_proc.id}"
                if regra_proc
                else f"proc:{proc_id}:{convenio_id or 0}:sem_regra"
            )
            det_proc = _obter_ou_criar_detalhe(entry, chave_proc, {
                "tipo_linha": "procedimento",
                "local_nome": local_nome,
                "procedimento_nome": proc["procedimento_nome"],
                "procedimento_id": proc_id,
                "convenio_nome": _rotulo_convenio_comissao(regra_proc, convenio_id),
                "vinculado_consulta": True,
                "qtd": 0,
                "valor_consulta": Decimal(0),
                "valor_procedimento": Decimal(0),
                "valor_total": Decimal(0),
                "comissao_consulta": Decimal(0),
                "comissao_procedimento": Decimal(0),
                "comissao": Decimal(0),
                "modo_consulta": "",
                "regra_consulta": "",
                "modo_procedimento": modo_pc,
                "regra_procedimento": regra_pc,
            })
            det_proc["qtd"] += 1
            det_proc["valor_procedimento"] += vp
            det_proc["valor_total"] += vp
            det_proc["comissao_procedimento"] += com_proc
            det_proc["comissao"] += com_proc

    profissionais = []
    for entry in prof_data.values():
        regras_por_local = {}
        for detalhe in entry["detalhes"]:
            if detalhe.get("tipo_linha") == "consulta" or detalhe.get("procedimento_nome") == LABEL_CONSULTA:
                ln = detalhe.get("local_nome") or "Geral"
                if detalhe.get("regra_consulta"):
                    regras_por_local[ln] = {
                        "local_nome": ln,
                        "modo": detalhe.get("modo_consulta", ""),
                        "regra": detalhe.get("regra_consulta", ""),
                    }
        entry["comissao_consulta_regras_por_local"] = list(regras_por_local.values())
        if len(regras_por_local) == 1:
            unica = next(iter(regras_por_local.values()))
            entry["comissao_consulta_regra"] = {
                "modo": unica["modo"],
                "regra": unica["regra"],
                "valor": 0,
            }
        for detalhe in entry["detalhes"]:
            del detalhe["_chave"]
        entry["detalhes"].sort(
            key=lambda d: (
                0 if d["procedimento_nome"] == LABEL_CONSULTA else 1,
                d.get("convenio_nome", ""),
                d["procedimento_nome"],
            ),
        )
        profissionais.append(entry)

    profissionais.sort(key=lambda p: p["nome"])

    return {
        "profissionais": profissionais,
        "totais": {
            "total_atendimentos": sum(p["total_atendimentos"] for p in profissionais),
            "valor_consulta": sum(p["valor_consulta"] for p in profissionais),
            "valor_procedimento": sum(p["valor_procedimento"] for p in profissionais),
            "valor_total": sum(p["valor_total"] for p in profissionais),
            "comissao_consulta": sum(p["comissao_consulta"] for p in profissionais),
            "comissao_procedimento": sum(p["comissao_procedimento"] for p in profissionais),
            "comissao_total": sum(p["comissao_total"] for p in profissionais),
        },
    }
