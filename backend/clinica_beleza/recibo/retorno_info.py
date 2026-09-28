"""Informações de retorno gratuito para exibição no recibo."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def montar_info_retorno_recibo(
    consulta,
    appointment=None,
    *,
    loja_id: int | None = None,
) -> dict[str, Any]:
    """Monta valor de tabela da consulta, prazo e texto de aviso para o recibo.

    Retorno:
      retorno_gratuito, taxa_consulta_referencia, retorno_dias, retorno_tipo, retorno_aviso
    """
    info: dict[str, Any] = {
        "retorno_gratuito": False,
        "taxa_consulta_referencia": 0.0,
        "retorno_dias": None,
        "retorno_tipo": "",
        "retorno_aviso": "",
    }
    if consulta is None and appointment is None:
        return info

    if appointment is None:
        appointment = getattr(consulta, "appointment", None)
    if consulta is None:
        consulta = getattr(appointment, "consulta", None)

    lid = loja_id or getattr(consulta, "loja_id", None) or getattr(appointment, "loja_id", None)
    if not lid:
        return info

    retorno_gratuito = bool(getattr(consulta, "retorno_gratuito", False)) if consulta else False
    retorno_tipo = (getattr(consulta, "retorno_tipo", None) or "") if consulta else ""
    info["retorno_gratuito"] = retorno_gratuito
    info["retorno_tipo"] = retorno_tipo

    local = None
    if consulta is not None:
        local = getattr(consulta, "local_atendimento", None)
    if local is None and appointment is not None:
        local = getattr(appointment, "local_atendimento", None)
    if local is not None:
        info["taxa_consulta_referencia"] = float(getattr(local, "valor_consulta", 0) or 0)
    if consulta is not None:
        vc = float(getattr(consulta, "valor_consulta", 0) or 0)
        if info["taxa_consulta_referencia"] <= 0 and vc > 0:
            info["taxa_consulta_referencia"] = vc

    dias, aviso = _resolver_prazo_e_aviso(
        lid,
        appointment=appointment,
        consulta=consulta,
        retorno_gratuito=retorno_gratuito,
        retorno_tipo=retorno_tipo,
        taxa_referencia=info["taxa_consulta_referencia"],
    )
    info["retorno_dias"] = dias
    info["retorno_aviso"] = aviso
    return info


def _aviso_taxa_descontada(dias: int, taxa: float, nome: str | None = None) -> str:
    from .moeda import formatar_moeda_recibo

    del nome  # a frase é a mesma com ou sem procedimento
    valor = f" de {formatar_moeda_recibo(taxa)}" if taxa > 0.009 else ""
    if dias > 0:
        prazo = f" Retorno gratuito em até {dias} dias após o atendimento."
    else:
        prazo = ""
    return f"A taxa de consulta{valor} foi integralmente descontada neste atendimento.{prazo}"


def _resolver_prazo_e_aviso(
    loja_id: int,
    *,
    appointment,
    consulta,
    retorno_gratuito: bool,
    retorno_tipo: str,
    taxa_referencia: float = 0.0,
) -> tuple[int | None, str]:
    try:
        from clinica_beleza.models import RetornoProcedimentoRegra
        from clinica_beleza.retorno_service import (
            _procedure_ids_from_appointment,
            _procedure_ids_from_consulta,
            get_agenda_retorno_config,
        )
    except Exception:
        logger.exception("Erro ao importar módulos de retorno para recibo")
        return None, ""

    try:
        config = get_agenda_retorno_config(loja_id)
    except Exception:
        logger.exception("Erro ao ler config de retorno loja_id=%s", loja_id)
        return None, ""

    proc_ids: set[int] = set()
    if appointment is not None:
        proc_ids |= _procedure_ids_from_appointment(appointment)
    if consulta is not None:
        proc_ids |= _procedure_ids_from_consulta(consulta)

    regras = []
    if config.retorno_procedimento_ativo and proc_ids:
        regras = list(
            RetornoProcedimentoRegra.objects.filter(
                loja_id=loja_id,
                is_active=True,
                procedure_id__in=proc_ids,
            ).select_related("procedure"),
        )

    dias_proc = max((int(r.dias_retorno) for r in regras), default=0) if regras else 0
    nomes_proc = [r.procedure.nome for r in regras if getattr(r, "procedure", None)]
    dias_cons = (
        int(config.dias_retorno_consulta or 0)
        if config.retorno_consulta_ativo and int(config.dias_retorno_consulta or 0) > 0
        else 0
    )

    taxa = float(taxa_referencia or 0)
    # Prazo aplicado neste atendimento (quando a taxa já foi descontada)
    if retorno_gratuito:
        if retorno_tipo == "procedimento" and dias_proc > 0:
            nome = nomes_proc[0] if len(nomes_proc) == 1 else "procedimento"
            return dias_proc, _aviso_taxa_descontada(dias_proc, taxa, nome)
        if dias_cons > 0:
            return dias_cons, _aviso_taxa_descontada(dias_cons, taxa)
        if dias_proc > 0:
            return dias_proc, _aviso_taxa_descontada(dias_proc, taxa)
        return None, _aviso_taxa_descontada(0, taxa)

    # Atendimento pago: informar política vigente para o cliente
    avisos: list[str] = []
    if dias_proc > 0:
        if len(nomes_proc) == 1:
            avisos.append(
                f"Este atendimento dá direito a retorno gratuito da taxa de consulta "
                f"em até {dias_proc} dias para acompanhamento de {nomes_proc[0]}.",
            )
        else:
            avisos.append(
                f"Este atendimento dá direito a retorno gratuito da taxa de consulta "
                f"em até {dias_proc} dias para acompanhamento do(s) procedimento(s).",
            )
    if dias_cons > 0:
        avisos.append(
            f"Este atendimento dá direito a retorno gratuito da taxa de consulta "
            f"em até {dias_cons} dias.",
        )
    if not avisos:
        return None, ""
    # Preferir o prazo mais relevante (procedimento > consulta) no campo dias
    dias = dias_proc or dias_cons or None
    return dias, " ".join(avisos)
