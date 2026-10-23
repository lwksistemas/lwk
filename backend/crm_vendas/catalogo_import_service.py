"""Grava o catálogo lido do PDF no cadastro da prestadora."""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .catalogo_pdf import CatalogoPdfError, pasta_do_pagamento, pasta_do_produto, pastas_do_item
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


def _ordem_pasta(nome: str) -> int:
    if nome in _ORDEM_PASTA:
        return _ORDEM_PASTA[nome]
    if nome.startswith("GRUPO "):
        resto = nome[6:]
        if resto.isdigit():
            return int(resto)
        if resto.startswith("D") and resto[1:].isdigit():
            return 10 + int(resto[1:])
    if nome.startswith("SEM "):
        return 20
    if nome.startswith("COM "):
        return 21
    if nome == "BOLETO BANCÁRIO":
        return 1
    if nome == "CARTÃO DE CRÉDITO":
        return 2
    return 0

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
    anterior = str(bruto.get("codigo_anterior") or "").strip()[:50]
    return {
        "codigo": codigo,
        "codigo_anterior": anterior if anterior and anterior != codigo else "",
        "nome": nome,
        "descricao": str(bruto.get("descricao") or "")[:4000],
        "preco": preco,
        "recorrencia": recorrencia,
        "tipo": tipo,
        "tabela": str(bruto.get("tabela") or "").strip().upper()[:30],
        "area": str(bruto.get("area") or "").strip().upper()[:40],
        "grupo": str(bruto.get("grupo") or "").strip().upper()[:8],
        "pagamento": str(bruto.get("pagamento") or "").strip().upper()[:20],
        "pastas": [str(nome)[:80] for nome in (bruto.get("pastas") or []) if str(nome).strip()][:4],
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
            ordem=_ordem_pasta(nome),
            ativo=True,
        )
    cache[chave] = pasta
    return pasta


def _produto_do_catalogo(loja_id, prestadora_id, item):
    """Acha o item pelo código curto ou pelo código longo da importação anterior."""
    curto = ProdutoServico.objects.filter(
        loja_id=loja_id,
        prestadora_id=prestadora_id,
        codigo=item["codigo"],
    ).first()
    anterior = item.get("codigo_anterior") or ""
    longo = None
    if anterior and anterior != item["codigo"]:
        longo = ProdutoServico.objects.filter(
            loja_id=loja_id,
            prestadora_id=prestadora_id,
            codigo=anterior,
        ).first()
    if longo is not None and curto is not None and longo.pk != curto.pk:
        longo.ativo = False
        longo.save(update_fields=["ativo"])
        return curto
    return longo or curto


def encurtar_codigos_anadem_gravados() -> int:
    """Troca no cadastro o código longo da ANADEM pelo código curto, no mesmo produto."""
    from .catalogo_pdf import encurtar_codigo_anadem

    alterados = 0
    for produto in ProdutoServico.objects.exclude(codigo="").iterator():
        novo = encurtar_codigo_anadem(produto.codigo or "")
        if not novo or novo == produto.codigo:
            continue
        ocupado = ProdutoServico.objects.filter(
            loja_id=produto.loja_id,
            prestadora_id=produto.prestadora_id,
            codigo=novo,
        ).exclude(pk=produto.pk).exists()
        if ocupado:
            continue
        produto.codigo = novo
        produto.save(update_fields=["codigo"])
        alterados += 1
    return alterados


def separar_grupos_nas_tabelas(loja_id: int) -> dict:
    """Cria GRUPO 1, GRUPO 2 e os demais dentro de cada tabela e move os serviços."""
    movidos = 0
    criadas = 0
    cache = {}
    tabelas = CategoriaProdutoServico.objects.filter(
        loja_id=loja_id,
        nome__istartswith="TABELA ",
    )
    for tabela in tabelas:
        produtos = ProdutoServico.objects.filter(loja_id=loja_id, categoria_id=tabela.id)
        for produto in produtos:
            nome_pasta = pasta_do_produto(produto.nome, produto.codigo)
            if not nome_pasta:
                continue
            ja_existia = (tabela.id, nome_pasta) in cache or CategoriaProdutoServico.objects.filter(
                loja_id=loja_id, pai_id=tabela.id, nome=nome_pasta,
            ).exists()
            destino = _garantir_pasta(loja_id, tabela, nome_pasta, cache)
            if not ja_existia:
                criadas += 1
            if produto.categoria_id != destino.id:
                produto.categoria = destino
                produto.save(update_fields=["categoria"])
                movidos += 1
    return {"pastas": criadas, "movidos": movidos}


def separar_pagamento_nos_grupos(loja_id: int) -> dict:
    """Dentro de cada grupo, separa boleto bancário e cartão de crédito."""
    movidos = 0
    criadas = 0
    cache = {}
    grupos = CategoriaProdutoServico.objects.filter(
        loja_id=loja_id,
        pai__nome__istartswith="TABELA ",
    )
    for grupo in grupos:
        if not (
            grupo.nome.startswith("GRUPO ")
            or grupo.nome.startswith("SEM PROCEDIMENTOS")
            or grupo.nome.startswith("COM PROCEDIMENTOS")
        ):
            continue
        produtos = ProdutoServico.objects.filter(loja_id=loja_id, categoria_id=grupo.id)
        for produto in produtos:
            nome_pasta = pasta_do_pagamento(produto.nome, produto.codigo)
            if not nome_pasta:
                continue
            ja_existia = (grupo.id, nome_pasta) in cache or CategoriaProdutoServico.objects.filter(
                loja_id=loja_id, pai_id=grupo.id, nome=nome_pasta,
            ).exists()
            destino = _garantir_pasta(loja_id, grupo, nome_pasta, cache)
            if not ja_existia:
                criadas += 1
            if produto.categoria_id != destino.id:
                produto.categoria = destino
                produto.save(update_fields=["categoria"])
                movidos += 1
    return {"pastas": criadas, "movidos": movidos}


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
            codigos.update(item["codigo_anterior"] for item in normalizados if item.get("codigo_anterior"))
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
            existente = _produto_do_catalogo(loja_id, prestadora.id, item)
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
            existente.codigo = dados["codigo"]
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
