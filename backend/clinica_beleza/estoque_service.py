"""Serviços de movimentação de estoque — Clínica da Beleza."""
import logging
from decimal import Decimal

from django.db import transaction

from .models import ConsultaProdutoUtilizado, MovimentacaoEstoque, ProdutoEstoque

logger = logging.getLogger(__name__)


def movimentar_saida(
    produto: ProdutoEstoque,
    quantidade: Decimal,
    *,
    motivo: str = '',
    profissional_id=None,
    appointment_id=None,
) -> MovimentacaoEstoque:
    """Registra saída e decrementa quantidade_atual (com lock de linha)."""
    if quantidade <= 0:
        raise ValueError('Quantidade deve ser maior que zero.')

    with transaction.atomic():
        produto = ProdutoEstoque.objects.select_for_update().get(pk=produto.pk)
        if produto.quantidade_atual < quantidade:
            raise ValueError(
                f'Estoque insuficiente para {produto.nome}. '
                f'Disponível: {produto.quantidade_atual} {produto.unidade_medida}.',
            )
        produto.quantidade_atual -= quantidade
        produto.save(update_fields=['quantidade_atual', 'updated_at'])
        return MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo='saida',
            quantidade=quantidade,
            motivo=motivo,
            profissional_id=profissional_id,
            appointment_id=appointment_id,
        )


def baixar_produtos_consulta(consulta) -> None:
    """
    Baixa estoque dos produtos registrados na consulta.
    Só executa itens com estoque_baixado=False.
    """
    itens = (
        ConsultaProdutoUtilizado.objects
        .filter(consulta=consulta, estoque_baixado=False)
        .select_related('produto')
    )
    if not itens.exists():
        return

    appointment_id = consulta.appointment_id
    profissional_id = consulta.professional_id

    with transaction.atomic():
        for item in itens:
            motivo = f'Uso na consulta #{consulta.id}'
            if item.lote:
                motivo += f' — lote {item.lote}'
            movimentar_saida(
                item.produto,
                item.quantidade,
                motivo=motivo,
                profissional_id=profissional_id,
                appointment_id=appointment_id,
            )
            item.estoque_baixado = True
            item.save(update_fields=['estoque_baixado'])
