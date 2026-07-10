"""Service para registrar movimentações de estoque."""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import MovimentacaoEstoque


class EstoqueMovimentacaoError(Exception):
    """Erro de validação na movimentação de estoque."""
    pass


def registrar_movimentacao(
    produto,
    tipo: str,
    quantidade_raw,
    motivo: str = '',
    profissional_id=None,
    appointment_id=None,
) -> MovimentacaoEstoque:
    """
    Registra entrada/saída/ajuste no estoque de um produto.

    Args:
        produto: instância de ProdutoEstoque
        tipo: 'entrada', 'saida' ou 'ajuste'
        quantidade_raw: valor da quantidade (será convertido para Decimal)
        motivo: texto livre (opcional)
        profissional_id: FK opcional
        appointment_id: FK opcional

    Returns:
        MovimentacaoEstoque criada

    Raises:
        EstoqueMovimentacaoError para validações de negócio
    """
    if tipo not in ('entrada', 'saida', 'ajuste'):
        raise EstoqueMovimentacaoError('Tipo deve ser: entrada, saida ou ajuste')

    try:
        quantidade = Decimal(str(quantidade_raw))
        if quantidade <= 0:
            raise EstoqueMovimentacaoError('Quantidade deve ser maior que zero')
    except (InvalidOperation, ValueError, TypeError):
        raise EstoqueMovimentacaoError('Quantidade inválida')

    if tipo == 'entrada':
        produto.quantidade_atual += quantidade
    elif tipo == 'saida':
        if produto.quantidade_atual < quantidade:
            raise EstoqueMovimentacaoError(
                f'Estoque insuficiente. Disponível: {produto.quantidade_atual} {produto.unidade_medida}'
            )
        produto.quantidade_atual -= quantidade
    elif tipo == 'ajuste':
        produto.quantidade_atual = quantidade

    with transaction.atomic():
        produto.save(update_fields=['quantidade_atual', 'updated_at'])

        mov = MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=tipo,
            quantidade=quantidade,
            motivo=motivo,
            profissional_id=profissional_id,
            appointment_id=appointment_id,
        )
    return mov
