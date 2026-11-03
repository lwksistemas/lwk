"""Saldo por lote. Não reescreve quantidade_atual nem movimentações antigas."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal


def consumir_lotes(lotes: list[dict], quantidade: Decimal) -> list[dict]:
    """Tira da validade mais próxima. Se o rastreado não cobrir, o resto fica sem lote."""
    restante = quantidade if quantidade > 0 else Decimal("0")
    ordenados = sorted(
        lotes,
        key=lambda lote: (lote.get("validade") is None, lote.get("validade") or date.min, lote.get("id") or 0),
    )
    saida = []
    for lote in ordenados:
        atual = Decimal(str(lote.get("quantidade") or "0"))
        toma = min(atual, restante) if restante > 0 else Decimal("0")
        novo = dict(lote)
        novo["quantidade"] = atual - toma
        restante -= toma
        saida.append(novo)
    return saida


def registrar_entrada_lote(produto, item: dict, quantidade: Decimal, validade) -> None:
    from .models import LoteProdutoEstoque

    codigo = (item.get("lote") or "").strip()[:50]
    if not codigo and not validade:
        return
    if quantidade <= 0:
        return
    documento = re.sub(r"\D", "", item.get("documento_fornecedor") or "")[:20]
    lote = LoteProdutoEstoque.objects.filter(produto=produto, codigo=codigo, validade=validade).first()
    if lote is None:
        lote = LoteProdutoEstoque(produto=produto, codigo=codigo, validade=validade, quantidade=Decimal("0"))
    lote.quantidade = (lote.quantidade or Decimal("0")) + quantidade
    lote.documento = documento
    lote.fornecedor_nome = (item.get("fornecedor") or "")[:200]
    lote.numero_nota = (item.get("numero_nota") or "")[:20]
    lote.chave = (item.get("chave") or "")[:44]
    lote.save()


def abater_lotes(produto, quantidade: Decimal) -> None:
    from django.db.models import F

    from .models import LoteProdutoEstoque

    if quantidade <= 0:
        return
    linhas = list(
        LoteProdutoEstoque.objects.select_for_update()
        .filter(produto=produto, quantidade__gt=0)
        .order_by(F("validade").asc(nulls_last=True), "id"),
    )
    if not linhas:
        return
    ajustados = consumir_lotes(
        [{"id": linha.id, "quantidade": linha.quantidade, "validade": linha.validade} for linha in linhas],
        quantidade,
    )
    por_id = {item["id"]: item["quantidade"] for item in ajustados}
    for linha in linhas:
        nova = por_id.get(linha.id)
        if nova is None or nova == linha.quantidade:
            continue
        linha.quantidade = nova
        linha.save(update_fields=["quantidade", "updated_at"])


def registrar_compra(item: dict, produto, fator: Decimal, quantidade: Decimal, custo: Decimal, validade, usuario: str) -> None:
    from .models import CompraFornecedorEstoque

    documento = re.sub(r"\D", "", item.get("documento_fornecedor") or "")[:20]
    data = None
    bruto = str(item.get("data_emissao") or "")[:10]
    if bruto:
        try:
            data = date.fromisoformat(bruto)
        except ValueError:
            data = None
    CompraFornecedorEstoque.objects.create(
        produto=produto,
        documento=documento,
        fornecedor_nome=(item.get("fornecedor") or "")[:200],
        codigo=(item.get("codigo_produto") or "")[:60],
        chave=(item.get("chave") or "")[:44],
        numero_nota=(item.get("numero_nota") or "")[:20],
        data_compra=data,
        quantidade=Decimal(str(item.get("quantidade") or "0")),
        unidade=(item.get("unidade_medida") or "")[:30],
        quantidade_estoque=quantidade,
        unidade_estoque=(item.get("unidade_estoque") or item.get("unidade_medida") or "")[:30],
        fator=fator,
        custo_unitario=custo,
        lote=(item.get("lote") or "")[:50],
        validade=validade,
        usuario=(usuario or "")[:80],
    )
