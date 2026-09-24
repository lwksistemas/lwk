"""Categorias configuráveis de procedimentos (catálogo por loja).

Procedure.categoria continua CharField (slug) — não mexe nos dados da Harmonis.
O catálogo só lista/renomeia/exclui nomes; o slug nos procedimentos permanece.
"""
from __future__ import annotations

import unicodedata
from collections import Counter

from django.db.models import Q
from django.utils.text import slugify

from .models import Procedure
from .models.procedures import CATEGORIAS_PROCEDIMENTO_PADRAO, CategoriaProcedimento

# Grafias da MESMA categoria (não misturar facial/corporal em "estetica").
CATEGORIA_SPELLINGS: dict[str, list[str]] = {
    "estetica": ["estetica", "estética", "Estética (geral)"],
    "soroterapia": ["soroterapia"],
    "facial": ["facial"],
    "corporal": ["corporal"],
    "capilar": ["capilar"],
    "depilacao": ["depilacao", "depilação"],
    "injetavel": ["injetavel", "injetável"],
    "geral": ["geral"],
    "protocolo": ["protocolo"],
    "outro": ["outro"],
}

# Módulo estética: especialidades irmãs. Só para ?modulo=
MODULE_CATEGORIA_ALIASES: dict[str, list[str]] = {
    "soroterapia": ["soroterapia", "soro"],
    "estetica": [
        "estetica", "estética", "facial", "corporal", "capilar",
        "depilacao", "depilação", "injetavel", "injetável",
    ],
}

PADRAO_POR_SLUG = dict(CATEGORIAS_PROCEDIMENTO_PADRAO)


class CategoriaProcedimentoError(Exception):
    """Erro de negócio ao gerir categoria de procedimento."""


def normalize_categoria(value: str) -> str:
    value = (value or "").lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn"
    )


def categoria_lookup_terms(categoria: str) -> list[str]:
    key = normalize_categoria(categoria)
    if not key:
        return []
    return list(CATEGORIA_SPELLINGS.get(key, [categoria, key]))


def filter_by_categoria_terms(queryset, terms: list[str], *, exact: bool):
    if not terms:
        return queryset
    q = Q()
    lookup = "categoria__iexact" if exact else "categoria__icontains"
    for term in terms:
        q |= Q(**{lookup: term})
    return queryset.filter(q)


def filter_procedures_by_categoria(queryset, categoria: str):
    """Filtra uma categoria específica (Estética geral ≠ Facial)."""
    terms = categoria_lookup_terms(categoria)
    return filter_by_categoria_terms(queryset, terms, exact=True)


def filter_procedures_by_modulo(queryset, modulo: str):
    """Filtra o módulo inteiro (estética inclui facial, corporal, etc.)."""
    modulo = (modulo or "").strip()
    if not modulo:
        return queryset
    key = normalize_categoria(modulo)
    aliases = MODULE_CATEGORIA_ALIASES.get(key, [modulo])
    return filter_by_categoria_terms(queryset, aliases, exact=False)


def slug_canonico(raw: str) -> str:
    """Normaliza valor gravado em Procedure.categoria para o slug do catálogo."""
    key = normalize_categoria(raw)
    if not key:
        return ""
    if key in CATEGORIA_SPELLINGS:
        return key
    for slug, spellings in CATEGORIA_SPELLINGS.items():
        if key in {normalize_categoria(s) for s in spellings}:
            return slug
    return slugify(key)[:50] or key[:50]


def _slug_unico(loja_id: int, base: str, *, exclude_pk: int | None = None) -> str:
    slug = (base or "categoria")[:50]
    n = 2
    while True:
        qs = CategoriaProcedimento.objects.filter(loja_id=loja_id, slug=slug)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return slug
        slug = f"{base[:45]}-{n}"
        n += 1


def _seed_padrao(loja_id: int) -> None:
    for ordem, (slug, nome) in enumerate(CATEGORIAS_PROCEDIMENTO_PADRAO, start=1):
        CategoriaProcedimento.objects.get_or_create(
            loja_id=loja_id,
            slug=slug,
            defaults={"nome": nome, "ordem": ordem, "cor": "#8B3D52", "is_active": True},
        )


def _importar_slugs_usados(loja_id: int) -> None:
    existentes = {
        normalize_categoria(s): s
        for s in CategoriaProcedimento.objects.filter(loja_id=loja_id).values_list("slug", flat=True)
    }
    usados = (
        Procedure.objects.filter(loja_id=loja_id)
        .exclude(categoria="")
        .values_list("categoria", flat=True)
        .distinct()
    )
    last = CategoriaProcedimento.objects.filter(loja_id=loja_id).order_by("-ordem").first()
    ordem = (last.ordem + 1) if last else 1
    for raw in usados:
        slug = slug_canonico(raw)
        if not slug or normalize_categoria(slug) in existentes:
            continue
        nome = PADRAO_POR_SLUG.get(slug) or (raw or slug).strip()[:100] or slug
        CategoriaProcedimento.objects.get_or_create(
            loja_id=loja_id,
            slug=slug,
            defaults={"nome": nome, "ordem": ordem, "cor": "#8B3D52", "is_active": True},
        )
        existentes[normalize_categoria(slug)] = slug
        ordem += 1


def _garantir_padrao_ausente(loja_id: int) -> None:
    """Inclui categorias padrão que a loja ainda não tem, sem alterar as existentes."""
    existentes = {
        normalize_categoria(slug)
        for slug in CategoriaProcedimento.objects.filter(loja_id=loja_id).values_list("slug", flat=True)
    }
    last = CategoriaProcedimento.objects.filter(loja_id=loja_id).order_by("-ordem").first()
    ordem = (last.ordem + 1) if last else 1
    for slug, nome in CATEGORIAS_PROCEDIMENTO_PADRAO:
        chave = normalize_categoria(slug)
        if chave in existentes:
            continue
        CategoriaProcedimento.objects.get_or_create(
            loja_id=loja_id,
            slug=slug,
            defaults={"nome": nome, "ordem": ordem, "cor": "#8B3D52", "is_active": True},
        )
        existentes.add(chave)
        ordem += 1


def garantir_categorias_procedimento(loja_id: int | None) -> None:
    """Cria o catálogo padrão e inclui slugs já usados nos procedimentos."""
    if not loja_id:
        return
    if not CategoriaProcedimento.objects.filter(loja_id=loja_id).exists():
        _seed_padrao(loja_id)
    else:
        _garantir_padrao_ausente(loja_id)
    _importar_slugs_usados(loja_id)


def _contagem_por_slug(loja_id: int | None) -> Counter[str]:
    qs = Procedure.objects.filter(is_active=True).exclude(categoria="")
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    counts: Counter[str] = Counter()
    for raw in qs.values_list("categoria", flat=True):
        counts[slug_canonico(raw) or normalize_categoria(raw)] += 1
    return counts


def categorias_com_contagem(loja_id: int | None):
    garantir_categorias_procedimento(loja_id)
    qs = CategoriaProcedimento.objects.filter(is_active=True).order_by("ordem", "nome")
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    cats = list(qs)
    counts = _contagem_por_slug(loja_id)
    for cat in cats:
        cat.procedimentos_count = counts.get(cat.slug, 0)
    return cats


def contar_procedimentos_ativos(categoria: CategoriaProcedimento) -> int:
    terms = categoria_lookup_terms(categoria.slug)
    qs = Procedure.objects.filter(is_active=True)
    if categoria.loja_id:
        qs = qs.filter(loja_id=categoria.loja_id)
    return filter_by_categoria_terms(qs, terms, exact=True).count()


def criar_categoria_procedimento(loja_id: int, *, nome: str, cor: str | None = None, ordem: int | None = None):
    nome = (nome or "").strip()
    if not nome:
        raise CategoriaProcedimentoError("Nome é obrigatório.")
    garantir_categorias_procedimento(loja_id)
    if CategoriaProcedimento.objects.filter(loja_id=loja_id, nome__iexact=nome).exists():
        raise CategoriaProcedimentoError("Já existe uma categoria com este nome.")
    base = slugify(normalize_categoria(nome))[:50] or "categoria"
    slug = _slug_unico(loja_id, base)
    if ordem is None:
        last = CategoriaProcedimento.objects.filter(loja_id=loja_id).order_by("-ordem").first()
        ordem = (last.ordem + 1) if last else 1
    obj = CategoriaProcedimento.objects.create(
        loja_id=loja_id,
        nome=nome,
        slug=slug,
        cor=cor or "#8B3D52",
        ordem=ordem,
        is_active=True,
    )
    obj.procedimentos_count = 0
    return obj


def atualizar_categoria_procedimento(obj: CategoriaProcedimento, *, nome: str | None = None, cor: str | None = None):
    if nome is not None:
        nome = nome.strip()
        if not nome:
            raise CategoriaProcedimentoError("Nome é obrigatório.")
        conflito = (
            CategoriaProcedimento.objects.filter(loja_id=obj.loja_id, nome__iexact=nome)
            .exclude(pk=obj.pk)
            .exists()
        )
        if conflito:
            raise CategoriaProcedimentoError("Já existe uma categoria com este nome.")
        obj.nome = nome
    if cor:
        obj.cor = cor
    obj.save()
    obj.procedimentos_count = contar_procedimentos_ativos(obj)
    return obj


def excluir_categoria_procedimento(obj: CategoriaProcedimento) -> None:
    ativos = contar_procedimentos_ativos(obj)
    if ativos:
        raise CategoriaProcedimentoError(
            f"Não é possível excluir: há {ativos} procedimento(s) nesta categoria.",
        )
    obj.delete()
