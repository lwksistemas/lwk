"""Helpers de categorias do estoque."""
from __future__ import annotations

from django.db.models import Count, Q

from .models.estoque import CATEGORIAS_ESTOQUE_PADRAO, CategoriaEstoque

_ALIASES = {
    "cosmetico": "cosmético",
    "Medicamentos": "medicamentos",
    "medicamento": "medicamentos",
}


def normalizar_slug_categoria(raw: str | None) -> str:
    s = (raw or "").strip()
    if not s:
        return "outro"
    return _ALIASES.get(s, s)


def garantir_categorias_estoque_padrao(loja_id: int | None) -> None:
    """Cria as 7 categorias padrão se a loja ainda não tiver nenhuma."""
    if not loja_id:
        return
    if CategoriaEstoque.objects.filter(loja_id=loja_id).exists():
        return
    for ordem, (slug, nome) in enumerate(CATEGORIAS_ESTOQUE_PADRAO, start=1):
        CategoriaEstoque.objects.get_or_create(
            loja_id=loja_id,
            slug=slug,
            defaults={"nome": nome, "ordem": ordem, "cor": "#8B3D52", "is_active": True},
        )


def resolver_categoria(
    *,
    loja_id: int | None,
    categoria_id: int | None = None,
    slug: str | None = None,
):
    """Resolve CategoriaEstoque por id ou slug (com seed se necessário)."""
    if loja_id:
        garantir_categorias_estoque_padrao(loja_id)
    if categoria_id:
        qs = CategoriaEstoque.objects.filter(pk=categoria_id)
        if loja_id:
            qs = qs.filter(loja_id=loja_id)
        cat = qs.first()
        if cat:
            return cat
    slug_n = normalizar_slug_categoria(slug)
    if loja_id:
        cat = CategoriaEstoque.objects.filter(loja_id=loja_id, slug=slug_n).first()
        if cat:
            return cat
        return CategoriaEstoque.objects.filter(loja_id=loja_id, slug="outro").first()
    return None


def categorias_com_contagem(loja_id: int | None = None):
    qs = (
        CategoriaEstoque.objects.filter(is_active=True)
        .annotate(produtos_count=Count("produtos", filter=Q(produtos__is_active=True)))
        .order_by("ordem", "nome")
    )
    if loja_id:
        qs = qs.filter(loja_id=loja_id)
    return qs
