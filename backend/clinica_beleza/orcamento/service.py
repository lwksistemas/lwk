"""CRUD de orçamentos de consulta."""
from decimal import Decimal

from clinica_beleza.models import Consulta, OrcamentoConsulta, OrcamentoItem, Procedure


def criar_orcamento(
    consulta_id: int,
    itens_payload: list[dict],
    observacoes: str = "",
    validade_dias: int = 30,
) -> OrcamentoConsulta:
    """Cria orçamento com itens a partir de uma consulta."""
    try:
        consulta = Consulta.objects.select_related("patient", "professional").get(id=consulta_id)
    except Consulta.DoesNotExist:
        raise ValueError("Consulta não encontrada.") from None

    orcamento = OrcamentoConsulta.objects.create(
        consulta=consulta,
        patient=consulta.patient,
        professional=consulta.professional,
        observacoes=observacoes,
        validade_dias=validade_dias,
        loja_id=consulta.loja_id,
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
            loja_id=consulta.loja_id,
        )
        valor_total += valor_custom * quantidade

    orcamento.valor_total = valor_total
    orcamento.save(update_fields=["valor_total"])
    return orcamento


def listar_orcamentos_consulta(consulta_id: int) -> list[dict]:
    """Retorna lista de orçamentos de uma consulta."""
    orcamentos = OrcamentoConsulta.objects.filter(consulta_id=consulta_id).prefetch_related("itens")
    resultado = []
    for orc in orcamentos:
        resultado.append({
            "id": orc.id,
            "consulta_id": orc.consulta_id,
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
        })
    return resultado


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
