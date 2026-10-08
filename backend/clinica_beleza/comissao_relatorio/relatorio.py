from datetime import date
from decimal import Decimal

from django.utils import timezone

from ..convenio_service import resolver_convenio_atendimento_comissao
from .alocacao import _alocar_valores_pagamento
from .finalizados import _valor_servico_atendimento, grupos_atendimentos_finalizados
from .constants import CHAVE_CONSULTA, LABEL_CONSULTA
from .formatting import _combinar_formas_pagamento, _formatar_regra
from .local_consulta import _resolver_local_atendimento_efetivo, _resolver_valor_consulta_cadastro
from .pagamentos import _obter_ou_criar_detalhe
from .procedimentos import _procedimentos_vinculados_consulta
from .regras import (
    _calcular_comissao_regra,
    _regras_profissional,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
    _rotulo_convenio_comissao,
)


def _conta_linha_consulta(regra_consulta, vc: Decimal, comissao_consulta: Decimal) -> bool:
    """A taxa só entra no relatório quando a profissional tem comissão de consulta."""
    return bool(regra_consulta) and (vc > 0 or comissao_consulta > 0)


def _quando_atendimento(appt) -> tuple[str, str]:
    dt = getattr(appt, "date", None)
    if dt is not None and timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    if not dt:
        return "—", "—"
    return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")


def _montar_linha_cliente(
    appt,
    consulta,
    *,
    local_nome,
    forma_pagamento,
    procedimentos,
    vp_map,
    regras,
    convenio_id,
    convenio_cache,
    vc,
    comissao_consulta,
    regra_cc,
) -> dict:
    """Um atendimento finalizado, com o nome da cliente e a comissão de cada serviço."""
    paciente = getattr(consulta, "patient", None) or getattr(appt, "patient", None)
    data_str, hora_str = _quando_atendimento(appt)
    linhas = []
    for proc in procedimentos:
        proc_id = proc["procedure_id"]
        vp = vp_map.get(proc_id, Decimal(0))
        regra_proc = _resolver_regra_procedimento(regras["procedimentos"], proc_id, convenio_id)
        com_proc = _calcular_comissao_regra(regra_proc, vp)
        _, regra_pc = _formatar_regra(regra_proc)
        linhas.append({
            "nome": proc["procedimento_nome"],
            "convenio_nome": _rotulo_convenio_comissao(regra_proc, convenio_id, convenio_cache),
            "valor": vp,
            "regra": regra_pc,
            "comissao": com_proc,
        })
    valor_proc = sum((linha["valor"] for linha in linhas), Decimal(0))
    comissao_proc = sum((linha["comissao"] for linha in linhas), Decimal(0))
    return {
        "data": data_str,
        "hora": hora_str,
        "paciente_nome": getattr(paciente, "nome", None) or "—",
        "forma_pagamento": forma_pagamento or "—",
        "local_nome": local_nome or "—",
        "valor_consulta": vc,
        "comissao_consulta": comissao_consulta,
        "regra_consulta": regra_cc,
        "procedimentos": linhas,
        "valor": vc + valor_proc,
        "comissao": comissao_consulta + comissao_proc,
    }


def _acumular_detalhe_consulta(entry, chave_consulta, vc, comissao_consulta, forma_pagamento, local_nome, modo_cc, regra_cc):
    """Atualiza (ou cria) o detalhe de linha de consulta no entry do profissional."""
    det = _obter_ou_criar_detalhe(entry, chave_consulta, {
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
    det["qtd"] += 1
    det["valor_consulta"] += vc
    det["valor_total"] += vc
    det["comissao_consulta"] += comissao_consulta
    det["comissao"] += comissao_consulta
    if forma_pagamento and forma_pagamento != "—":
        pagamentos_atuais = [
            p.strip() for p in (det.get("forma_pagamento") or "").split(" + ")
            if p.strip() and p.strip() != "—"
        ]
        for label in forma_pagamento.split(" + "):
            if label and label not in pagamentos_atuais:
                pagamentos_atuais.append(label)
        det["forma_pagamento"] = " + ".join(pagamentos_atuais) if pagamentos_atuais else forma_pagamento


def _acumular_detalhe_procedimento(entry, proc, vp, com_proc, convenio_id, regras, local_nome, convenio_cache=None):
    """Atualiza (ou cria) o detalhe de linha de procedimento no entry do profissional."""
    proc_id = proc["procedure_id"]
    regra_proc = _resolver_regra_procedimento(regras["procedimentos"], proc_id, convenio_id)
    com_proc = _calcular_comissao_regra(regra_proc, vp)
    modo_pc, regra_pc = _formatar_regra(regra_proc)
    chave_proc = (
        f"proc:{proc_id}:{convenio_id or 0}:{regra_proc.id}"
        if regra_proc
        else f"proc:{proc_id}:{convenio_id or 0}:sem_regra"
    )
    det = _obter_ou_criar_detalhe(entry, chave_proc, {
        "tipo_linha": "procedimento",
        "local_nome": local_nome,
        "procedimento_nome": proc["procedimento_nome"],
        "procedimento_id": proc_id,
        "convenio_nome": _rotulo_convenio_comissao(regra_proc, convenio_id, convenio_cache),
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
    det["qtd"] += 1
    det["valor_procedimento"] += vp
    det["valor_total"] += vp
    det["comissao_procedimento"] += com_proc
    det["comissao"] += com_proc
    return com_proc


def _acumular_entry_prof(prof_data, prof_id, prof_nome, amount, vc, vp_map, comissao_consulta, comissao_procedimentos):
    """Inicializa ou acumula os totais do profissional em prof_data."""
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
            "clientes": [],
        }
    entry = prof_data[prof_id]
    entry["total_atendimentos"] += 1
    entry["valor_consulta"] += vc
    entry["valor_procedimento"] += sum(vp_map.values())
    entry["valor_total"] += amount
    entry["comissao_consulta"] += comissao_consulta
    entry["comissao_procedimento"] += comissao_procedimentos
    entry["comissao_total"] += comissao_consulta + comissao_procedimentos
    return entry


def _finalizar_profissionais(prof_data):
    """Monta regras por local, ordena detalhes e retorna lista de profissionais."""
    profissionais = []
    for entry in prof_data.values():
        regras_por_local = {}
        for detalhe in entry["detalhes"]:
            if detalhe.get("tipo_linha") == "consulta" or detalhe.get("procedimento_nome") == LABEL_CONSULTA:
                ln = detalhe.get("local_nome") or "Geral"
                if detalhe.get("regra_consulta"):
                    regras_por_local[ln] = {"local_nome": ln, "modo": detalhe.get("modo_consulta", ""), "regra": detalhe.get("regra_consulta", "")}
        entry["comissao_consulta_regras_por_local"] = list(regras_por_local.values())
        if len(regras_por_local) == 1:
            unica = next(iter(regras_por_local.values()))
            entry["comissao_consulta_regra"] = {"modo": unica["modo"], "regra": unica["regra"], "valor": 0}
        for detalhe in entry["detalhes"]:
            del detalhe["_chave"]
        entry["detalhes"].sort(key=lambda d: (0 if d["procedimento_nome"] == LABEL_CONSULTA else 1, d.get("convenio_nome", ""), d["procedimento_nome"]))
        profissionais.append(entry)
    profissionais = [p for p in profissionais if p["comissao_total"] > 0]
    profissionais.sort(key=lambda p: p["nome"])
    return profissionais


def _processar_grupo_pagamento(grupo, consulta_map, prof_data, regras_cache, convenio_cache=None):
    """Processa um grupo de pagamentos e acumula dados do profissional."""
    appt = grupo["appointment"]
    if not appt:
        return
    consulta = consulta_map.get(appt.id)
    if not consulta:
        return
    profissional = grupo.get("profissional") or appt.professional
    if profissional is None:
        return
    procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
    if not procedimentos and grupo["total_amount"] <= 0:
        return
    prof_id = profissional.id
    amount = grupo["total_amount"]
    if prof_id not in regras_cache:
        regras_cache[prof_id] = _regras_profissional(prof_id)
    regras = regras_cache[prof_id]
    valor_consulta_cad = _resolver_valor_consulta_cadastro(consulta, amount, procedimentos, regras)
    proc_com_regra = regras.get("procedimento_ids") or set()
    convenio_id = resolver_convenio_atendimento_comissao(appt, consulta, procedimentos)
    vc, vp_map = _alocar_valores_pagamento(amount, valor_consulta_cad, procedimentos, proc_com_regra)
    local_id, local_nome = _resolver_local_atendimento_efetivo(consulta, regras, valor_consulta_cad)
    regra_consulta = _resolver_regra_consulta(regras, local_id)
    forma_pagamento = _combinar_formas_pagamento(grupo["payments"])
    comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
    comissao_procedimentos = sum(
        _calcular_comissao_regra(
            _resolver_regra_procedimento(regras["procedimentos"], p["procedure_id"], convenio_id),
            vp_map.get(p["procedure_id"], Decimal(0)),
        )
        for p in procedimentos
    )
    entry = _acumular_entry_prof(
        prof_data, prof_id, profissional.nome, amount, vc, vp_map,
        comissao_consulta, comissao_procedimentos,
    )
    modo_cc, regra_cc = _formatar_regra(regra_consulta)
    inclui_consulta = _conta_linha_consulta(regra_consulta, vc, comissao_consulta)
    if inclui_consulta:
        _acumular_detalhe_consulta(
            entry, f"{local_nome}||{CHAVE_CONSULTA}", vc, comissao_consulta,
            forma_pagamento, local_nome, modo_cc, regra_cc,
        )
    for proc in procedimentos:
        vp = vp_map.get(proc["procedure_id"], Decimal(0))
        _acumular_detalhe_procedimento(entry, proc, vp, Decimal(0), convenio_id, regras, local_nome, convenio_cache)
    entry["clientes"].append(_montar_linha_cliente(
        appt, consulta,
        local_nome=local_nome,
        forma_pagamento=forma_pagamento,
        procedimentos=procedimentos,
        vp_map=vp_map,
        regras=regras,
        convenio_id=convenio_id,
        convenio_cache=convenio_cache,
        vc=vc if inclui_consulta else Decimal(0),
        comissao_consulta=comissao_consulta if inclui_consulta else Decimal(0),
        regra_cc=regra_cc if inclui_consulta else "",
    ))


def comissao_do_atendimento(appt, consulta, *, regras_cache: dict) -> Decimal:
    """Comissão do serviço finalizado. Não usa o valor já gravado no pagamento.

    Atendimento a prazo fica com comissao_valor 0 no lançamento. A regra da
    profissional continua valendo, como no relatório de comissões.
    """
    if not appt or not consulta:
        return Decimal(0)
    profissional = getattr(appt, "professional", None) or getattr(consulta, "professional", None)
    if profissional is None:
        return Decimal(0)
    procedimentos = _procedimentos_vinculados_consulta(appt, consulta)
    amount = _valor_servico_atendimento(consulta, procedimentos)
    if amount <= 0 and not procedimentos:
        return Decimal(0)
    prof_id = profissional.id
    if prof_id not in regras_cache:
        regras_cache[prof_id] = _regras_profissional(prof_id)
    regras = regras_cache[prof_id]
    valor_consulta_cad = _resolver_valor_consulta_cadastro(consulta, amount, procedimentos, regras)
    proc_com_regra = regras.get("procedimento_ids") or set()
    convenio_id = resolver_convenio_atendimento_comissao(appt, consulta, procedimentos)
    vc, vp_map = _alocar_valores_pagamento(
        amount, valor_consulta_cad, procedimentos, proc_com_regra,
    )
    local_id, _local_nome = _resolver_local_atendimento_efetivo(consulta, regras, valor_consulta_cad)
    regra_consulta = _resolver_regra_consulta(regras, local_id)
    comissao_consulta = _calcular_comissao_regra(regra_consulta, vc)
    if not _conta_linha_consulta(regra_consulta, vc, comissao_consulta):
        comissao_consulta = Decimal(0)
    comissao_procedimentos = sum(
        (
            _calcular_comissao_regra(
                _resolver_regra_procedimento(regras["procedimentos"], p["procedure_id"], convenio_id),
                vp_map.get(p["procedure_id"], Decimal(0)),
            )
            for p in procedimentos
        ),
        Decimal(0),
    )
    return (comissao_consulta + comissao_procedimentos).quantize(Decimal("0.01"))


def calcular_comissoes(
    *,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    professional_id: int | None = None,
) -> dict:
    """Calcula comissões dos profissionais.

    Entra toda consulta finalizada no período do atendimento. O valor é o do
    serviço. Pagamento pendente ou a prazo não tira a comissão: o prejuízo
    de quem não paga fica com a clínica.
    """
    grupos, consulta_map = grupos_atendimentos_finalizados(
        data_inicio=data_inicio,
        data_fim=data_fim,
        professional_id=professional_id,
    )

    prof_data = {}
    regras_cache = {}
    convenio_cache: dict = {}

    for grupo in grupos:
        _processar_grupo_pagamento(grupo, consulta_map, prof_data, regras_cache, convenio_cache)

    profissionais = _finalizar_profissionais(prof_data)

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
