"""CRUD de orçamentos de consulta."""
from decimal import Decimal

from clinica_beleza.models import Consulta, OrcamentoConsulta, OrcamentoItem, Patient, Procedure, Professional


def criar_orcamento(
    consulta_id: int | None,
    itens_payload: list[dict],
    observacoes: str = "",
    validade_dias: int = 30,
    *,
    patient_id: int | None = None,
    professional_id: int | None = None,
) -> OrcamentoConsulta:
    """Cria orçamento dentro de um atendimento ou só para o cliente."""
    consulta = None
    if consulta_id:
        try:
            consulta = Consulta.objects.select_related("patient", "professional").get(id=consulta_id)
        except Consulta.DoesNotExist:
            raise ValueError("Consulta não encontrada.") from None
        patient = consulta.patient
        professional = consulta.professional
        loja_id = consulta.loja_id
    else:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            raise ValueError("Cliente não encontrado.") from None
        professional = None
        if professional_id:
            professional = Professional.objects.filter(id=professional_id).first()
        loja_id = patient.loja_id

    orcamento = OrcamentoConsulta.objects.create(
        consulta=consulta,
        patient=patient,
        professional=professional,
        observacoes=observacoes,
        validade_dias=validade_dias,
        loja_id=loja_id,
    )

    valor_total = Decimal("0.00")
    for item_data in itens_payload:
        try:
            procedure = Procedure.objects.get(id=item_data["procedure_id"])
        except Procedure.DoesNotExist:
            orcamento.delete()
            raise ValueError("Procedimento não encontrado.") from None
        valor_custom = Decimal(str(item_data.get("valor_customizado") or procedure.preco))
        quantidade = int(item_data.get("quantidade", 1))

        OrcamentoItem.objects.create(
            orcamento=orcamento,
            procedure=procedure,
            nome_procedimento=procedure.nome,
            descricao_procedimento=procedure.descricao or "",
            valor_original=procedure.preco,
            valor_customizado=valor_custom,
            quantidade=quantidade,
            observacao_item=item_data.get("observacao_item", ""),
            loja_id=loja_id,
        )
        valor_total += valor_custom * quantidade

    orcamento.valor_total = valor_total
    orcamento.save(update_fields=["valor_total"])
    return orcamento


def buscar_clientes_orcamento(termo: str) -> list[dict]:
    """Clientes ativos para o orçamento avulso."""
    from clinica_beleza.patient_search import apply_patient_search

    termo = (termo or "").strip()
    if len(termo) < 2:
        return []
    qs = apply_patient_search(Patient.objects.filter(is_active=True), termo).order_by("nome")[:20]
    return [{"id": p.id, "nome": p.nome, "cpf": p.cpf or ""} for p in qs]


def listar_orcamentos_paciente(patient_id: int) -> list[dict]:
    """Todos os orçamentos do cliente, com ou sem atendimento."""
    orcamentos = (
        OrcamentoConsulta.objects.filter(patient_id=patient_id)
        .select_related("patient", "professional")
        .prefetch_related("itens")
    )
    return [_serializar_orcamento(orc) for orc in orcamentos]


def listar_orcamentos_consulta(consulta_id: int) -> list[dict]:
    """Orçamentos do cliente da consulta, inclusive os feitos fora do atendimento."""
    patient_id = Consulta.objects.filter(id=consulta_id).values_list("patient_id", flat=True).first()
    if not patient_id:
        return []
    return listar_orcamentos_paciente(patient_id)


def _serializar_orcamento(orc: OrcamentoConsulta) -> dict:
    return {
        "id": orc.id,
        "consulta_id": orc.consulta_id,
        "patient_id": orc.patient_id,
        "patient_name": orc.patient.nome if orc.patient else "",
        "professional_name": orc.professional.nome if orc.professional else "",
        "observacoes": orc.observacoes,
        "valor_total": str(orc.valor_total),
        "validade_dias": orc.validade_dias,
        "status": orc.status,
        "enviado_email": orc.enviado_email,
        "enviado_whatsapp": orc.enviado_whatsapp,
        "data_envio": orc.data_envio.isoformat() if orc.data_envio else None,
        "created_at": orc.created_at.isoformat(),
        "itens": [
            {
                "id": item.id,
                "procedure_id": item.procedure_id,
                "nome_procedimento": item.nome_procedimento,
                "valor_original": str(item.valor_original),
                "valor_customizado": str(item.valor_customizado),
                "quantidade": item.quantidade,
                "observacao_item": item.observacao_item,
                "subtotal": str(item.subtotal),
            }
            for item in orc.itens.all()
        ],
    }


def atualizar_status_orcamento(orcamento: OrcamentoConsulta, novo_status: str) -> OrcamentoConsulta:
    """Marca orçamento como ACEITO ou RECUSADO (RASCUNHO/ENVIADO ou troca entre os dois)."""
    novo = (novo_status or "").strip().upper()
    if novo not in ("ACEITO", "RECUSADO"):
        raise ValueError("Status deve ser ACEITO ou RECUSADO.")
    if orcamento.status not in ("RASCUNHO", "ENVIADO", "ACEITO", "RECUSADO"):
        raise ValueError(f"Não é possível alterar orçamento com status {orcamento.status}.")
    if orcamento.status == novo:
        return orcamento
    orcamento.status = novo
    orcamento.save(update_fields=["status", "updated_at"])
    return orcamento


def excluir_orcamento(orcamento: OrcamentoConsulta) -> None:
    """Exclui orçamento (aceito permanece no histórico)."""
    if orcamento.status == "ACEITO":
        raise ValueError("Não é possível excluir um orçamento aceito.")
    orcamento.delete()
