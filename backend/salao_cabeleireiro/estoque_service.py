"""Venda do caixa. O estoque baixa uma vez, na confirmação, e volta no estorno."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone


def banco_da_loja():
    from tenants.middleware import get_current_tenant_db

    banco = get_current_tenant_db()
    return banco if banco and banco != "default" else None


def tenant_atomic():
    """select_for_update só vale na conexão do schema da loja."""
    banco = banco_da_loja()
    if banco:
        return transaction.atomic(using=banco)
    return transaction.atomic()


def gravar(modelo, **kwargs):
    banco = banco_da_loja()
    if banco:
        return modelo.objects.using(banco).create(**kwargs)
    return modelo.objects.create(**kwargs)

from .caixa_service import comissao_do_atendimento, interpretar_formas, motivo_bloqueio_recebimento, quantia, rotulo_formas
from .models import MovimentoEstoque, Produto, Recebimento, Venda, VendaItem


def agrupar_pedidos(brutos) -> list[dict]:
    if not brutos:
        return []
    if not isinstance(brutos, list):
        raise ValueError("Informe os produtos da venda.")
    grupos = {}
    for item in brutos:
        if not isinstance(item, dict):
            raise ValueError("Informe o produto e a quantidade.")
        try:
            produto_id = int(item.get("produto"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Escolha o produto.") from exc
        try:
            quantidade = int(item.get("quantidade") or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError("Informe a quantidade inteira.") from exc
        if quantidade <= 0:
            raise ValueError("A quantidade precisa ser maior que zero.")
        grupos[produto_id] = grupos.get(produto_id, 0) + quantidade
    return [{"produto": chave, "quantidade": valor} for chave, valor in grupos.items()]


def repartir_pagamento(partes, valor_servico: Decimal) -> tuple[list[dict], list[dict]]:
    """As primeiras formas cobrem o serviço. O que sobra fica no produto."""
    restante = quantia(valor_servico)
    servico = []
    produto = []
    for parte in partes:
        valor = quantia(parte["valor"])
        forma = parte["forma"]
        if restante <= 0:
            produto.append({"forma": forma, "valor": f"{valor:.2f}"})
            continue
        if valor <= restante:
            servico.append({"forma": forma, "valor": f"{valor:.2f}"})
            restante -= valor
            continue
        servico.append({"forma": forma, "valor": f"{restante:.2f}"})
        produto.append({"forma": forma, "valor": f"{(valor - restante):.2f}"})
        restante = Decimal("0")
    return servico, produto


def _baixar(produto, quantidade, venda):
    if produto.saldo < quantidade:
        raise ValueError(f"{produto.nome} tem {produto.saldo} no estoque.")
    produto.saldo -= quantidade
    produto.save(update_fields=["saldo"])
    gravar(
        MovimentoEstoque,
        produto=produto,
        venda=venda,
        tipo="saida",
        quantidade=-quantidade,
        saldo_depois=produto.saldo,
    )


def registrar_venda(dados, agendamento, papel: str, local: str, origem: str) -> Venda:
    pedidos = agrupar_pedidos(dados.get("itens") or dados.get("produtos"))
    if agendamento is None and not pedidos:
        raise ValueError("Escolha um atendimento ou um produto.")
    if agendamento is not None:
        if agendamento.status != "COMPLETED":
            raise ValueError("Conclua o atendimento antes de receber.")
        if any(item.is_active for item in agendamento.recebimentos.all()):
            raise ValueError("Este atendimento já foi recebido.")
        motivo = motivo_bloqueio_recebimento(local, origem, papel)
        if motivo:
            raise PermissionError(motivo)
    with tenant_atomic():
        bloqueados = Produto.objects.none()
        if pedidos:
            bloqueados = Produto.objects.select_for_update().filter(id__in=[pedido["produto"] for pedido in pedidos], is_active=True)
        produtos = {item.id: item for item in bloqueados}
        if len(produtos) != len(pedidos):
            raise ValueError("Um dos produtos não está mais à venda.")
        for pedido in pedidos:
            produto = produtos[pedido["produto"]]
            if produto.saldo < pedido["quantidade"]:
                raise ValueError(f"{produto.nome} tem {produto.saldo} no estoque.")
        desconto = quantia(dados.get("desconto") or 0) if agendamento is not None else Decimal("0")
        if agendamento is not None:
            valor_servico, comissao, percentual = comissao_do_atendimento(
                agendamento.profissional,
                agendamento.servico_id,
                agendamento.servico.preco,
                desconto,
            )
        else:
            valor_servico, comissao = Decimal("0"), Decimal("0")
        valor_produtos = sum(
            (quantia(produtos[pedido["produto"]].preco) * pedido["quantidade"] for pedido in pedidos),
            Decimal("0"),
        ).quantize(Decimal("0.01"))
        total = (valor_servico + valor_produtos).quantize(Decimal("0.01"))
        partes = interpretar_formas(dados, total)
        partes_servico, partes_produtos = repartir_pagamento(partes, valor_servico)
        recebimento = None
        if agendamento is not None:
            recebimento = gravar(
                Recebimento,
                agendamento=agendamento,
                profissional=agendamento.profissional,
                valor_servico=agendamento.servico.preco,
                desconto=desconto,
                valor=valor_servico,
                forma=partes_servico[0]["forma"] if partes_servico else (partes[0]["forma"] if partes else "dinheiro"),
                partes=partes_servico,
                comissao_percentual=percentual,
                comissao_valor=comissao,
                observacao=(dados.get("observacao") or "")[:200],
            )
        ultimo = Venda.objects.select_for_update().order_by("-numero").first()
        venda = gravar(
            Venda,
            numero=(ultimo.numero if ultimo else 0) + 1,
            agendamento=agendamento,
            recebimento=recebimento,
            cliente_nome=agendamento.cliente.nome if agendamento is not None else (dados.get("cliente_nome") or "")[:160],
            valor_servico=valor_servico,
            valor_produtos=valor_produtos,
            desconto=desconto,
            valor=total,
            forma=partes[0]["forma"] if partes else "dinheiro",
            partes=partes,
            partes_produtos=partes_produtos,
        )
        for pedido in pedidos:
            produto = produtos[pedido["produto"]]
            preco = quantia(produto.preco)
            total_item = (preco * pedido["quantidade"]).quantize(Decimal("0.01"))
            comissao_item = (total_item * quantia(produto.comissao_percentual) / Decimal("100")).quantize(Decimal("0.01"))
            gravar(
                VendaItem,
                venda=venda,
                produto=produto,
                nome=produto.nome,
                quantidade=pedido["quantidade"],
                preco=preco,
                total=total_item,
                comissao_valor=comissao_item,
                estoque_baixado=True,
            )
            _baixar(produto, pedido["quantidade"], venda)
        return venda


def estornar_venda(venda: Venda):
    if venda is None or not venda.is_active:
        return
    with tenant_atomic():
        venda = Venda.objects.select_for_update().get(pk=venda.pk)
        if not venda.is_active:
            return
        for item in venda.itens.select_related("produto").all():
            if not item.estoque_baixado:
                continue
            produto = Produto.objects.select_for_update().get(pk=item.produto_id)
            produto.saldo += item.quantidade
            produto.save(update_fields=["saldo"])
            gravar(
                MovimentoEstoque,
                produto=produto,
                venda=venda,
                tipo="estorno",
                quantidade=item.quantidade,
                saldo_depois=produto.saldo,
            )
            item.estoque_baixado = False
            item.save(update_fields=["estoque_baixado"])
        venda.is_active = False
        venda.save(update_fields=["is_active"])


def publico_venda(venda: Venda) -> dict:
    return {
        "numero": venda.numero,
        "cliente": venda.cliente_nome or "Consumidor",
        "valor": f"{quantia(venda.valor):.2f}",
        "forma_label": rotulo_formas(venda.partes, venda.forma),
        "quando": timezone.localtime(venda.created_at).strftime("%d/%m/%Y %H:%M"),
        "itens": [
            {"nome": item.nome, "quantidade": item.quantidade, "total": f"{quantia(item.total):.2f}"}
            for item in venda.itens.all()
        ],
    }


def nome_comercial(valor: str) -> str:
    """Nome do estoque, do caixa e do recibo. A clínica grava em maiúsculas."""
    return (valor or "").strip().upper()[:200]


def nome_fornecedor(valor: str) -> str:
    return (valor or "").strip().upper()[:100]


def publico_produto(produto: Produto) -> dict:
    return {
        "id": produto.id,
        "nome": produto.nome,
        "fornecedor": produto.fornecedor,
        "codigo_barras": produto.codigo_barras,
        "preco": f"{quantia(produto.preco):.2f}",
        "saldo": produto.saldo,
        "comissao_percentual": f"{quantia(produto.comissao_percentual):.2f}",
    }
