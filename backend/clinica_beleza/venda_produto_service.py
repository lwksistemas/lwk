"""Venda de produto. O insumo do procedimento não passa por aqui."""
from __future__ import annotations

from decimal import Decimal


class VendaProdutoError(ValueError):
    """A venda pedida não pode sair do estoque nem entrar no recibo."""


def subtotal_item(quantidade, preco_unitario, desconto) -> Decimal:
    """Quantidade vezes o preço, menos o desconto da linha. Nunca negativo."""
    bruto = Decimal(str(quantidade or 0)) * Decimal(str(preco_unitario or 0))
    liquido = bruto - Decimal(str(desconto or 0))
    return liquido if liquido > 0 else Decimal("0")


def validar_item_venda(produto, quantidade, lotes, *, hoje=None) -> None:
    """Produto inativo, sem permissão de venda ou sem saldo utilizável não sai."""
    from .estoque_lotes import saldo_utilizavel

    if not getattr(produto, "is_active", True):
        raise VendaProdutoError(f"{produto.nome} está inativo.")
    if not getattr(produto, "vende_ao_cliente", False):
        raise VendaProdutoError(f"{produto.nome} não está liberado para venda.")
    qtd = Decimal(str(quantidade or 0))
    if qtd <= 0:
        raise VendaProdutoError("Quantidade deve ser maior que zero.")
    preco = Decimal(str(getattr(produto, "preco_venda", 0) or 0))
    if preco < 0:
        raise VendaProdutoError("Preço de venda inválido.")
    livre = saldo_utilizavel(
        getattr(produto, "quantidade_atual", 0),
        lotes,
        ativo=True,
        hoje=hoje,
    )
    if qtd > livre:
        raise VendaProdutoError(
            f"Saldo utilizável de {produto.nome} é {livre}. Lote vencido não entra nessa conta.",
        )


def linha_recibo(nome: str, quantidade, preco_unitario, desconto) -> dict:
    qtd = Decimal(str(quantidade or 0))
    preco = Decimal(str(preco_unitario or 0))
    desc = Decimal(str(desconto or 0))
    quantidade_texto = f"{qtd:.2f}".rstrip("0").rstrip(".")
    return {
        "nome": nome,
        "quantidade": quantidade_texto or "0",
        "preco_unitario": float(preco),
        "desconto": float(desc),
        "subtotal": float(subtotal_item(qtd, preco, desc)),
    }


def total_vendas_consulta(consulta) -> Decimal:
    """Soma só o que foi vendido. Uso no procedimento fica de fora e vale zero."""
    from .models import ConsultaProdutoUtilizado

    total = Decimal("0")
    itens = ConsultaProdutoUtilizado.objects.filter(
        consulta=consulta, finalidade="venda", estornado=False,
    )
    for item in itens:
        total += subtotal_item(item.quantidade, item.preco_unitario, item.desconto)
    return total


def produtos_da_consulta(consulta) -> list[dict]:
    from .models import ConsultaProdutoUtilizado

    linhas = []
    itens = (
        ConsultaProdutoUtilizado.objects.filter(consulta=consulta, finalidade="venda", estornado=False)
        .select_related("produto")
    )
    for item in itens:
        linhas.append(linha_recibo(item.produto.nome, item.quantidade, item.preco_unitario, item.desconto))
    return linhas


def produtos_da_venda(venda) -> list[dict]:
    linhas = []
    for item in venda.itens.select_related("produto").all():
        if item.estornado:
            continue
        linhas.append(linha_recibo(item.produto.nome, item.quantidade, item.preco_unitario, item.desconto))
    return linhas


def produtos_do_pagamento(payment) -> list[dict]:
    venda = getattr(payment, "venda_balcao", None)
    if venda is not None and venda.status != "cancelada":
        return produtos_da_venda(venda)
    appointment = getattr(payment, "appointment", None)
    consulta = getattr(appointment, "consulta", None) if appointment is not None else None
    if consulta is None:
        return []
    return produtos_da_consulta(consulta)


def _lotes_do_produto(produto) -> list[dict]:
    from .models import LoteProdutoEstoque

    return [
        {"quantidade": lote.quantidade, "validade": lote.validade}
        for lote in LoteProdutoEstoque.objects.filter(produto=produto, quantidade__gt=0)
    ]


def registrar_venda_balcao(*, loja_id, paciente, itens: list[dict], payment_method: str):
    """Cria a venda, o pagamento e a baixa numa transação só."""
    from django.utils.timezone import now

    from .estoque_service import movimentar_saida, tenant_atomic
    from .models import Patient, Payment, ProdutoEstoque, VendaBalcao, VendaBalcaoItem

    if not itens:
        raise VendaProdutoError("Informe ao menos um produto.")
    metodo = (payment_method or "CASH").strip().upper()
    metodos = {codigo for codigo, _rotulo in Payment.PAYMENT_METHOD_CHOICES}
    if metodo not in metodos or metodo == "DESPESA":
        raise VendaProdutoError("Forma de pagamento inválida.")

    with tenant_atomic():
        cliente = Patient.objects.filter(pk=paciente, loja_id=loja_id).first()
        if cliente is None:
            raise VendaProdutoError("Cliente não encontrado nesta clínica.")
        preparados = []
        total = Decimal("0")
        ja_pedido: dict[int, Decimal] = {}
        for bruto in itens:
            produto = ProdutoEstoque.objects.select_for_update().filter(
                pk=bruto.get("produto"), loja_id=loja_id,
            ).first()
            if produto is None:
                raise VendaProdutoError("Produto não encontrado nesta clínica.")
            quantidade = Decimal(str(bruto.get("quantidade") or 0))
            preco = Decimal(str(bruto.get("preco_unitario") if bruto.get("preco_unitario") not in (None, "") else produto.preco_venda or 0))
            desconto = Decimal(str(bruto.get("desconto") or 0))
            if desconto < 0 or preco < 0:
                raise VendaProdutoError("Preço e desconto não podem ser negativos.")
            acumulado = ja_pedido.get(produto.pk, Decimal("0")) + quantidade
            validar_item_venda(produto, acumulado, _lotes_do_produto(produto))
            ja_pedido[produto.pk] = acumulado
            if desconto > preco * quantidade:
                raise VendaProdutoError(f"Desconto maior que o valor de {produto.nome}.")
            preparados.append((produto, quantidade, preco, desconto))
            total += subtotal_item(quantidade, preco, desconto)
        if total <= 0:
            raise VendaProdutoError("O total da venda precisa ser maior que zero.")

        payment = Payment.objects.create(
            appointment=None,
            amount=total if metodo != "PRAZO" else Decimal("0"),
            valor_total=total,
            valor_produtos=total,
            payment_method=metodo,
            status="PENDING" if metodo == "PRAZO" else "PAID",
            payment_date=None if metodo == "PRAZO" else now(),
            loja_id=loja_id,
            notes="Venda de produtos. Recibo comercial, não é nota fiscal.",
        )
        venda = VendaBalcao.objects.create(
            paciente=cliente, payment=payment, status=VendaBalcao.STATUS_CONCLUIDA, loja_id=loja_id,
        )
        for produto, quantidade, preco, desconto in preparados:
            item = VendaBalcaoItem.objects.create(
                venda=venda,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=preco,
                desconto=desconto,
                loja_id=loja_id,
            )
            movimentar_saida(
                produto,
                quantidade,
                motivo=f"Venda de produto #{venda.id}",
            )
            item.estoque_baixado = True
            item.save(update_fields=["estoque_baixado"])
        return venda


def cancelar_venda_balcao(venda) -> None:
    """Devolve a quantidade ao saldo e cancela o pagamento. O histórico das duas movimentações fica."""
    from .estoque_movimentacao_service import registrar_movimentacao
    from .estoque_service import tenant_atomic
    from .models import VendaBalcao

    if venda.status == VendaBalcao.STATUS_CANCELADA:
        raise VendaProdutoError("Esta venda já foi cancelada.")
    with tenant_atomic():
        for item in venda.itens.select_related("produto"):
            if item.estornado or not item.estoque_baixado:
                continue
            registrar_movimentacao(
                item.produto,
                "entrada",
                item.quantidade,
                motivo=f"Estorno da venda #{venda.id}",
            )
            item.estornado = True
            item.save(update_fields=["estornado"])
        venda.status = VendaBalcao.STATUS_CANCELADA
        venda.save(update_fields=["status"])
        payment = venda.payment
        if payment is not None and payment.status != "CANCELLED":
            payment.status = "CANCELLED"
            payment.save(update_fields=["status", "updated_at"])


def estornar_vendas_da_consulta(consulta) -> None:
    """Devolve só o produto vendido. O insumo usado no procedimento permanece baixado."""
    from .estoque_movimentacao_service import registrar_movimentacao
    from .models import ConsultaProdutoUtilizado

    itens = ConsultaProdutoUtilizado.objects.filter(
        consulta=consulta, finalidade="venda", estoque_baixado=True, estornado=False,
    ).select_related("produto")
    for item in itens:
        registrar_movimentacao(
            item.produto,
            "entrada",
            item.quantidade,
            motivo=f"Estorno da venda na consulta #{consulta.id}",
        )
        item.estornado = True
        item.save(update_fields=["estornado"])
