from decimal import Decimal


def _distribuir_proporcional(amount: Decimal, procedimentos: list[dict]) -> dict[int, Decimal]:
    """Distribui amount proporcionalmente aos valores dos procedimentos, com ajuste de centavo."""
    soma = sum(p["valor"] for p in procedimentos)
    if soma <= 0:
        return {p["procedure_id"]: Decimal(0) for p in procedimentos}
    ratio = amount / soma
    result = {p["procedure_id"]: (p["valor"] * ratio).quantize(Decimal("0.01")) for p in procedimentos}
    ajuste = amount - sum(result.values())
    if ajuste and procedimentos:
        result[procedimentos[-1]["procedure_id"]] += ajuste
    return result


def _distribuir_uniforme(amount: Decimal, procedimentos: list[dict]) -> dict[int, Decimal]:
    """Distribui amount igualmente entre os procedimentos quando não há valores base."""
    if not procedimentos:
        return {}
    parte = (amount / len(procedimentos)).quantize(Decimal("0.01"))
    result = {}
    restante = amount
    for i, p in enumerate(procedimentos):
        if i == len(procedimentos) - 1:
            result[p["procedure_id"]] = restante
        else:
            result[p["procedure_id"]] = parte
            restante -= parte
    return result


def _distribuir_com_protegidos(
    amount: Decimal,
    valor_consulta: Decimal,
    procedimentos: list[dict],
    com_regra: set[int],
) -> tuple[Decimal, dict[int, Decimal]] | None:
    """Tenta alocar valor consulta fixo + protegidos fixos + distribui restante.
    Retorna None se a condição de proteção não se aplicar.
    """
    soma_proc = sum(p["valor"] for p in procedimentos)
    if not (valor_consulta > 0 and soma_proc > 0 and amount >= valor_consulta):
        return None
    protegidos = [p for p in procedimentos if p["procedure_id"] in com_regra]
    outros = [p for p in procedimentos if p["procedure_id"] not in com_regra]
    soma_protegida = sum(p["valor"] for p in protegidos)
    if protegidos and valor_consulta + soma_protegida <= amount:
        proc_map = {p["procedure_id"]: p["valor"] for p in protegidos}
        proc_map.update(_distribuir_proporcional(amount - valor_consulta - soma_protegida, outros))
        return valor_consulta, proc_map
    return valor_consulta, _distribuir_proporcional(amount - valor_consulta, procedimentos)


def _alocar_valores_pagamento(
    amount: Decimal,
    valor_consulta: Decimal,
    procedimentos: list[dict],
    proc_ids_com_regra: set[int] | None = None,
) -> tuple[Decimal, dict[int, Decimal]]:
    """Distribui o valor pago entre consulta e cada procedimento.
    Retorna (valor_consulta_alocado, {procedure_id: valor_procedimento}).

    Procedimentos com regra de comissão mantêm o valor cadastrado; a taxa de
    consulta e o ajuste proporcional incidem nos demais.
    """
    if amount <= 0:
        return Decimal(0), {p["procedure_id"]: Decimal(0) for p in procedimentos}

    soma_proc = sum(p["valor"] for p in procedimentos)
    com_regra = proc_ids_com_regra or set()

    resultado_protegidos = _distribuir_com_protegidos(amount, valor_consulta, procedimentos, com_regra)
    if resultado_protegidos is not None:
        return resultado_protegidos

    if valor_consulta > 0 and amount < valor_consulta:
        return amount, {p["procedure_id"]: Decimal(0) for p in procedimentos}

    esperado = valor_consulta + soma_proc
    if esperado <= 0:
        return Decimal(0), _distribuir_uniforme(amount, procedimentos)

    if esperado == amount:
        return valor_consulta, {p["procedure_id"]: p["valor"] for p in procedimentos}

    ratio = amount / esperado
    vc = (valor_consulta * ratio).quantize(Decimal("0.01"))
    proc_map = {p["procedure_id"]: (p["valor"] * ratio).quantize(Decimal("0.01")) for p in procedimentos}
    ajuste = amount - vc - sum(proc_map.values())
    if proc_map:
        proc_map[procedimentos[-1]["procedure_id"]] += ajuste
    else:
        vc += ajuste
    return vc, proc_map
