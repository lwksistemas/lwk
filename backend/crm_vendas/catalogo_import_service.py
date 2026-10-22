"""Grava o catálogo lido do PDF na categoria escolhida de produtos e serviços."""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .catalogo_pdf import CatalogoPdfError
from .models import CategoriaProdutoServico, ProdutoServico

_RECORRENCIAS = {codigo for codigo, _rotulo in ProdutoServico.RECORRENCIA_CHOICES}
_TIPOS = {codigo for codigo, _rotulo in ProdutoServico.TIPO_CHOICES}


def _item_normalizado(bruto: dict) -> dict:
    if not isinstance(bruto, dict):
        raise CatalogoPdfError("Item inválido na lista.")
    codigo = str(bruto.get("codigo") or "").strip()[:50]
    nome = str(bruto.get("nome") or "").strip()[:255]
    if not codigo or not nome:
        raise CatalogoPdfError("Cada item precisa de código e nome.")
    try:
        preco = Decimal(str(bruto.get("preco") or "0").replace(",", "."))
    except InvalidOperation as exc:
        raise CatalogoPdfError(f"Preço inválido no item {codigo}.") from exc
    if preco < 0:
        raise CatalogoPdfError(f"Preço inválido no item {codigo}.")
    recorrencia = str(bruto.get("recorrencia") or "unico")
    if recorrencia not in _RECORRENCIAS:
        recorrencia = "unico"
    tipo = str(bruto.get("tipo") or "servico")
    if tipo not in _TIPOS:
        tipo = "servico"
    return {
        "codigo": codigo,
        "nome": nome,
        "descricao": str(bruto.get("descricao") or "")[:4000],
        "preco": preco,
        "recorrencia": recorrencia,
        "tipo": tipo,
    }


def importar_catalogo_na_categoria(loja_id: int, categoria_id: int, itens: list, substituir: bool = False) -> dict:
    categoria = CategoriaProdutoServico.objects.filter(pk=categoria_id, loja_id=loja_id).first()
    if categoria is None:
        raise CatalogoPdfError("Escolha uma categoria de produtos e serviços desta loja.")
    if not itens:
        raise CatalogoPdfError("Nenhum item para importar.")
    if len(itens) > 2000:
        raise CatalogoPdfError("No máximo 2000 itens por importação.")
    normalizados = [_item_normalizado(item) for item in itens]
    criados = 0
    atualizados = 0
    with transaction.atomic():
        if substituir:
            codigos = {item["codigo"] for item in normalizados}
            (
                ProdutoServico.objects.filter(loja_id=loja_id, categoria_id=categoria.id)
                .exclude(codigo__in=codigos)
                .update(ativo=False)
            )
        for item in normalizados:
            existente = ProdutoServico.objects.filter(loja_id=loja_id, codigo=item["codigo"]).first()
            if existente is None:
                ProdutoServico.objects.create(
                    loja_id=loja_id,
                    categoria=categoria,
                    ativo=True,
                    **item,
                )
                criados += 1
                continue
            existente.nome = item["nome"]
            existente.descricao = item["descricao"]
            existente.preco = item["preco"]
            existente.recorrencia = item["recorrencia"]
            existente.tipo = item["tipo"]
            existente.categoria = categoria
            existente.ativo = True
            existente.save()
            atualizados += 1
    return {
        "criados": criados,
        "atualizados": atualizados,
        "total": criados + atualizados,
        "categoria_id": categoria.id,
        "categoria_nome": categoria.nome,
    }
