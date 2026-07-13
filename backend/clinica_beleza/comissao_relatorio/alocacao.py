from decimal import Decimal


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

    if valor_consulta > 0 and soma_proc > 0 and amount >= valor_consulta:
        protegidos = [p for p in procedimentos if p["procedure_id"] in com_regra]
        outros = [p for p in procedimentos if p["procedure_id"] not in com_regra]
        soma_protegida = sum(p["valor"] for p in protegidos)

        if protegidos and valor_consulta + soma_protegida <= amount:
            proc_map = {p["procedure_id"]: p["valor"] for p in protegidos}
            restante_outros = amount - valor_consulta - soma_protegida
            if outros:
                soma_outros = sum(p["valor"] for p in outros)
                if soma_outros > 0:
                    ratio = restante_outros / soma_outros
                    for p in outros:
                        proc_map[p["procedure_id"]] = (p["valor"] * ratio).quantize(Decimal("0.01"))
                    ajuste = restante_outros - sum(
                        proc_map[p["procedure_id"]] for p in outros
                    )
                    if ajuste:
                        proc_map[outros[-1]["procedure_id"]] += ajuste
            return valor_consulta, proc_map

        restante_proc = amount - valor_consulta
        ratio = restante_proc / soma_proc
        proc_map = {
            p["procedure_id"]: (p["valor"] * ratio).quantize(Decimal("0.01"))
            for p in procedimentos
        }
        ajuste = restante_proc - sum(proc_map.values())
        if proc_map:
            ultimo_id = procedimentos[-1]["procedure_id"]
            proc_map[ultimo_id] += ajuste
        return valor_consulta, proc_map

    if valor_consulta > 0 and amount < valor_consulta:
        return amount, {p["procedure_id"]: Decimal(0) for p in procedimentos}

    esperado = valor_consulta + soma_proc

    if esperado <= 0:
        if not procedimentos:
            return amount, {}
        parte = (amount / len(procedimentos)).quantize(Decimal("0.01"))
        resultado = {}
        restante = amount
        for i, p in enumerate(procedimentos):
            if i == len(procedimentos) - 1:
                resultado[p["procedure_id"]] = restante
            else:
                resultado[p["procedure_id"]] = parte
                restante -= parte
        return Decimal(0), resultado

    if esperado == amount:
        return valor_consulta, {p["procedure_id"]: p["valor"] for p in procedimentos}

    ratio = amount / esperado
    vc = (valor_consulta * ratio).quantize(Decimal("0.01"))
    proc_map = {
        p["procedure_id"]: (p["valor"] * ratio).quantize(Decimal("0.01"))
        for p in procedimentos
    }
    ajuste = amount - vc - sum(proc_map.values())
    if proc_map:
        ultimo_id = procedimentos[-1]["procedure_id"]
        proc_map[ultimo_id] += ajuste
    else:
        vc += ajuste
    return vc, proc_map
