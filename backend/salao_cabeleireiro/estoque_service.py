"""Venda do caixa. O estoque baixa uma vez, na confirmação, e volta no estorno."""
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
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

from .caixa_service import (
    comissao_do_atendimento,
    fatiar_partes,
    interpretar_formas,
    motivo_bloqueio_recebimento,
    quantia,
    repartir_desconto,
    rotulo_formas,
    validar_documentos,
)
from .models import MovimentoEstoque, Produto, Recebimento, SessaoCaixa, Venda, VendaItem


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


def registrar_venda(dados, agendamentos, papel: str, local: str, origem: str, operador: str = "") -> Venda:
    """Um pagamento pode quitar vários serviços do mesmo cliente. Produto entra no mesmo recibo."""
    agendamentos = list(agendamentos or [])
    pedidos = agrupar_pedidos(dados.get("itens") or dados.get("produtos"))
    if not agendamentos and not pedidos:
        raise ValueError("Escolha um atendimento ou um produto.")
    if agendamentos:
        clientes = {item.cliente_id for item in agendamentos}
        if len(clientes) > 1:
            raise ValueError("Receba um cliente por vez.")
        motivo = motivo_bloqueio_recebimento(local, origem, papel)
        if motivo:
            raise PermissionError(motivo)
        for agendamento in agendamentos:
            if agendamento.status != "COMPLETED":
                raise ValueError("Conclua o atendimento antes de receber.")
            if any(item.is_active for item in agendamento.recebimentos.all()):
                raise ValueError("Este atendimento já foi recebido.")
    tem_servico = bool(agendamentos)
    tem_produto = bool(pedidos)
    validar_documentos(tem_servico, tem_produto, dados)
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
        descontos = repartir_desconto(
            [item.servico.preco for item in agendamentos],
            (dados.get("desconto") or 0) if agendamentos else 0,
        )
        recibos_previstos = []
        for agendamento, desconto_item in zip(agendamentos, descontos):
            valor_item, comissao, percentual = comissao_do_atendimento(
                agendamento.profissional,
                agendamento.servico_id,
                agendamento.servico.preco,
                desconto_item,
            )
            recibos_previstos.append((agendamento, desconto_item, valor_item, comissao, percentual))
        valor_servico = sum((item[2] for item in recibos_previstos), Decimal("0")).quantize(Decimal("0.01"))
        desconto = sum(descontos, Decimal("0")).quantize(Decimal("0.01")) if descontos else Decimal("0")
        valor_produtos = sum(
            (quantia(produtos[pedido["produto"]].preco) * pedido["quantidade"] for pedido in pedidos),
            Decimal("0"),
        ).quantize(Decimal("0.01"))
        total = (valor_servico + valor_produtos).quantize(Decimal("0.01"))
        from .formas_service import codigos_ativos

        partes = interpretar_formas(dados, total, codigos_ativos())
        partes_servico, partes_produtos = repartir_pagamento(partes, valor_servico)
        fatias = fatiar_partes(partes_servico, [item[2] for item in recibos_previstos])
        recebimentos = []
        for indice, (agendamento, desconto_item, valor_item, comissao, percentual) in enumerate(recibos_previstos):
            fatia = fatias[indice] if indice < len(fatias) else []
            recebimentos.append(gravar(
                Recebimento,
                agendamento=agendamento,
                profissional=agendamento.profissional,
                valor_servico=agendamento.servico.preco,
                desconto=desconto_item,
                valor=valor_item,
                forma=fatia[0]["forma"] if fatia else (partes[0]["forma"] if partes else "dinheiro"),
                partes=fatia,
                comissao_percentual=percentual,
                comissao_valor=comissao,
                observacao=(dados.get("observacao") or "")[:200],
            ))
        recebimento = recebimentos[0] if recebimentos else None
        primeiro = agendamentos[0] if agendamentos else None
        sessao = SessaoCaixa.objects.select_for_update().filter(is_active=True).order_by("-id").first()
        if sessao is None:
            sessao = gravar(SessaoCaixa, operador_nome=(operador or "")[:160])
        ultimo = Venda.objects.select_for_update().order_by("-numero").first()
        venda = gravar(
            Venda,
            numero=(ultimo.numero if ultimo else 0) + 1,
            agendamento=primeiro,
            recebimento=recebimento,
            operador_nome=(operador or "")[:160],
            sessao=sessao,
            cliente_nome=primeiro.cliente.nome if primeiro is not None else (dados.get("cliente_nome") or "")[:160],
            valor_servico=valor_servico,
            valor_produtos=valor_produtos,
            desconto=desconto,
            valor=total,
            forma=partes[0]["forma"] if partes else "dinheiro",
            partes=partes,
            partes_produtos=partes_produtos,
        )
        if recebimentos:
            Recebimento.objects.filter(pk__in=[item.pk for item in recebimentos]).update(venda=venda)
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
        from .comprovante_layout import congelar_venda

        itens = list(venda.itens.all())
        venda.comprovante = congelar_venda(venda, recebimentos, itens)
        venda.save(update_fields=["comprovante"])
        return venda


def estornar_operacao(recebimento):
    """Um pagamento com vários serviços se desfaz por inteiro, junto com o estoque."""
    if recebimento is None or not recebimento.is_active:
        return
    with tenant_atomic():
        venda = None
        if getattr(recebimento, "venda_id", None):
            candidata = recebimento.venda
            if candidata is not None and candidata.is_active:
                venda = candidata
        if venda is None:
            venda = Venda.objects.filter(recebimento=recebimento, is_active=True).first()
        if venda is not None:
            estornar_venda(venda)
            Recebimento.objects.filter(is_active=True).filter(
                Q(pk=recebimento.pk) | Q(venda=venda) | Q(pk=venda.recebimento_id)
            ).update(is_active=False)
            return
        recebimento.is_active = False
        recebimento.save(update_fields=["is_active"])


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
    recibos = list(
        Recebimento.objects.filter(venda=venda).select_related("agendamento__servico", "profissional")
    )
    if not recibos and venda.recebimento_id:
        recibos = [venda.recebimento]
    from .comprovante_layout import comprovante_da_venda

    comprovante = comprovante_da_venda(venda)
    return {
        "numero": venda.numero,
        "cliente": venda.cliente_nome or "Consumidor",
        "valor": f"{quantia(venda.valor):.2f}",
        "desconto": f"{quantia(venda.desconto):.2f}",
        "operador": venda.operador_nome,
        "estornado": not venda.is_active,
        "forma_label": rotulo_formas(venda.partes, venda.forma),
        "quando": timezone.localtime(venda.created_at).strftime("%d/%m/%Y %H:%M"),
        "servicos": [
            {
                "nome": item.agendamento.servico.nome,
                "profissional": item.profissional.nome,
                "total": f"{quantia(item.valor):.2f}",
            }
            for item in recibos
        ],
        "itens": [
            {"nome": item.nome, "quantidade": item.quantidade, "total": f"{quantia(item.total):.2f}"}
            for item in venda.itens.all()
        ],
        "formas": comprovante.get("formas") or [],
        "comprovante": comprovante,
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
