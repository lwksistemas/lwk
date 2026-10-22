"""Grava o catálogo lido do PDF no cadastro da prestadora."""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .catalogo_pdf import CatalogoPdfError, pastas_do_item
from .models import CategoriaProdutoServico, Conta, ProdutoServico

_COR_PASTA = {
    "MEDICINA": "#0F766E",
    "ODONTOLOGIA": "#0369A1",
    "DEMAIS CATEGORIAS": "#6B7280",
    "TABELA BLUE": "#2563EB",
    "TABELA GREEN": "#15803D",
    "TABELA BLACK": "#111827",
    "TABELA ESSENCIAL": "#7C3AED",
}
_ORDEM_PASTA = {
    "MEDICINA": 10,
    "ODONTOLOGIA": 20,
    "DEMAIS CATEGORIAS": 30,
    "TABELA BLUE": 10,
    "TABELA GREEN": 20,
    "TABELA BLACK": 30,
    "TABELA ESSENCIAL": 40,
}

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
        "tabela": str(bruto.get("tabela") or "").strip().upper()[:30],
        "area": str(bruto.get("area") or "").strip().upper()[:40],
        "pastas": [str(nome)[:80] for nome in (bruto.get("pastas") or []) if str(nome).strip()][:3],
    }


def _raiz_categoria(categoria):
    atual = categoria
    for _ in range(6):
        if atual is None or not atual.pai_id:
            return atual
        atual = atual.pai
    return atual


def _garantir_pasta(loja_id, pai, nome, cache):
    chave = (pai.id, nome)
    if chave in cache:
        return cache[chave]
    pasta = CategoriaProdutoServico.objects.filter(loja_id=loja_id, pai_id=pai.id, nome=nome).first()
    if pasta is None:
        pasta = CategoriaProdutoServico.objects.create(
            loja_id=loja_id,
            pai=pai,
            nome=nome,
            cor=_COR_PASTA.get(nome, pai.cor or "#3B82F6"),
            ordem=_ORDEM_PASTA.get(nome, 0),
            ativo=True,
        )
    cache[chave] = pasta
    return pasta


def _destino_categoria(loja_id, categoria, item, cache):
    if categoria is None:
        return None
    atual = _raiz_categoria(categoria)
    for nome in pastas_do_item(item):
        atual = _garantir_pasta(loja_id, atual, nome, cache)
    return atual


def importar_catalogo_na_categoria(
    loja_id: int,
    itens: list,
    prestadora_id: int,
    categoria_id: int | None = None,
    substituir: bool = False,
) -> dict:
    prestadora = Conta.objects.filter(pk=prestadora_id, loja_id=loja_id).first()
    if prestadora is None or prestadora.tipo not in ("prestadora", "ambos"):
        raise CatalogoPdfError("Escolha a prestadora dona deste catálogo.")
    categoria = None
    if categoria_id:
        categoria = (
            CategoriaProdutoServico.objects.select_related("pai", "pai__pai")
            .filter(pk=categoria_id, loja_id=loja_id)
            .first()
        )
        if categoria is None:
            raise CatalogoPdfError("A categoria escolhida não é desta loja.")
    if not itens:
        raise CatalogoPdfError("Nenhum item para importar.")
    if len(itens) > 2000:
        raise CatalogoPdfError("No máximo 2000 itens por importação.")
    normalizados = [_item_normalizado(item) for item in itens]
    criados = 0
    atualizados = 0
    pastas = {}
    with transaction.atomic():
        if substituir:
            codigos = {item["codigo"] for item in normalizados}
            (
                ProdutoServico.objects.filter(loja_id=loja_id, prestadora_id=prestadora.id)
                .exclude(codigo__in=codigos)
                .update(ativo=False)
            )
        for item in normalizados:
            destino = _destino_categoria(loja_id, categoria, item, pastas)
            dados = {
                "codigo": item["codigo"],
                "nome": item["nome"],
                "descricao": item["descricao"],
                "preco": item["preco"],
                "recorrencia": item["recorrencia"],
                "tipo": item["tipo"],
            }
            existente = ProdutoServico.objects.filter(
                loja_id=loja_id,
                prestadora_id=prestadora.id,
                codigo=item["codigo"],
            ).first()
            if existente is None:
                ProdutoServico.objects.create(
                    loja_id=loja_id,
                    prestadora=prestadora,
                    categoria=destino,
                    ativo=True,
                    **dados,
                )
                criados += 1
                continue
            existente.nome = dados["nome"]
            existente.descricao = dados["descricao"]
            existente.preco = dados["preco"]
            existente.recorrencia = dados["recorrencia"]
            existente.tipo = dados["tipo"]
            if destino is not None:
                existente.categoria = destino
            existente.prestadora = prestadora
            existente.ativo = True
            existente.save()
            atualizados += 1
    return {
        "criados": criados,
        "atualizados": atualizados,
        "total": criados + atualizados,
        "prestadora_id": prestadora.id,
        "prestadora_nome": prestadora.nome or prestadora.razao_social,
        "categoria_id": categoria.id if categoria else None,
        "categoria_nome": categoria.nome if categoria else "",
    }
