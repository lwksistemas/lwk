"""Serviços de movimentação de estoque — Clínica da Beleza."""
import logging
from decimal import Decimal

from django.db import transaction

from .models import ConsultaProdutoUtilizado, MovimentacaoEstoque, ProdutoEstoque

logger = logging.getLogger(__name__)


def tenant_atomic():
    """atomic() no schema da loja — obrigatório para select_for_update multi-tenant."""
    from tenants.middleware import get_current_tenant_db

    db = get_current_tenant_db()
    if db and db != "default":
        return transaction.atomic(using=db)
    return transaction.atomic()


def movimentar_saida(
    produto: ProdutoEstoque,
    quantidade: Decimal,
    *,
    motivo: str = "",
    profissional_id=None,
    appointment_id=None,
    permitir_saldo_negativo: bool = False,
) -> MovimentacaoEstoque:
    """Registra saída e decrementa quantidade_atual (com lock de linha)."""
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    with tenant_atomic():
        produto = ProdutoEstoque.objects.select_for_update().get(pk=produto.pk)
        if not permitir_saldo_negativo and produto.quantidade_atual < quantidade:
            raise ValueError(
                f"Estoque insuficiente para {produto.nome}. "
                f"Disponível: {produto.quantidade_atual} {produto.unidade_medida}.",
            )
        if permitir_saldo_negativo and produto.quantidade_atual < quantidade:
            logger.warning(
                "Baixa consulta com saldo negativo: %s (disp. %s, saída %s)",
                produto.nome,
                produto.quantidade_atual,
                quantidade,
            )
        produto.quantidade_atual -= quantidade
        produto.save(update_fields=["quantidade_atual", "updated_at"])
        return MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo="saida",
            quantidade=quantidade,
            motivo=motivo,
            profissional_id=profissional_id,
            appointment_id=appointment_id,
        )


def produtos_estoque_insuficiente(consulta) -> list[str]:
    """Lista produtos da consulta (ainda não baixados) cujo estoque atual é menor
    que a quantidade total registrada (soma por produto).
    """
    from collections import defaultdict

    itens = (
        ConsultaProdutoUtilizado.objects
        .filter(consulta=consulta, estoque_baixado=False)
        .select_related("produto")
    )
    totais: dict[int, dict] = defaultdict(
        lambda: {"nome": "", "unidade": "", "necessario": Decimal(0), "disponivel": Decimal(0)},
    )
    for item in itens:
        bucket = totais[item.produto_id]
        bucket["nome"] = item.produto.nome
        bucket["unidade"] = item.produto.unidade_medida
        bucket["necessario"] += item.quantidade
        bucket["disponivel"] = item.produto.quantidade_atual

    erros: list[str] = []
    for data in totais.values():
        if data["disponivel"] < data["necessario"]:
            erros.append(
                f"{data['nome']}: necessário {data['necessario']} {data['unidade']}, "
                f"disponível {data['disponivel']} {data['unidade']}",
            )
    return erros


def baixar_produtos_consulta(consulta) -> None:
    """Baixa estoque dos produtos registrados na consulta.
    Só executa itens com estoque_baixado=False.
    """
    itens = (
        ConsultaProdutoUtilizado.objects
        .filter(consulta=consulta, estoque_baixado=False)
        .select_related("produto")
    )
    if not itens.exists():
        return

    appointment_id = consulta.appointment_id
    profissional_id = consulta.professional_id

    with tenant_atomic():
        for item in itens:
            motivo = f"Uso na consulta #{consulta.id}"
            if item.lote:
                motivo += f" — lote {item.lote}"
            movimentar_saida(
                item.produto,
                item.quantidade,
                motivo=motivo,
                profissional_id=profissional_id,
                appointment_id=appointment_id,
            )
            item.estoque_baixado = True
            item.save(update_fields=["estoque_baixado"])
