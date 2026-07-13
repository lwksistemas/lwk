from decimal import Decimal


def _procedimentos_vinculados_consulta(appt, consulta) -> list[dict]:
    """Procedimentos do agendamento vinculado à consulta (N procedimentos por atendimento)."""
    aps = list(appt.appointment_procedures.select_related("procedure").order_by("ordem", "id"))
    items = []
    for ap in aps:
        items.append({
            "procedure_id": ap.procedure_id,
            "procedimento_nome": ap.procedure.nome,
            "valor": ap.valor or ap.procedure.preco or Decimal(0),
        })
    if items:
        return items

    if appt.procedure_id and appt.procedure:
        return [{
            "procedure_id": appt.procedure_id,
            "procedimento_nome": appt.procedure.nome,
            "valor": appt.procedure.preco or Decimal(0),
        }]

    if consulta.procedure_id and consulta.procedure:
        return [{
            "procedure_id": consulta.procedure_id,
            "procedimento_nome": consulta.procedure.nome,
            "valor": consulta.procedure.preco or Decimal(0),
        }]
    return []
