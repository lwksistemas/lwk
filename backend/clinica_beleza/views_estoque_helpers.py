"""Helpers de listagem/paginação/filtro de produtos de estoque."""
from .estoque_categorias import normalizar_slug_categoria
from .pagination import paginate_queryset

# Campos para listagem via .values() (inclui numero_nota desde migration 0034).
_PRODUTO_VALUES_FIELDS = (
    "id", "nome", "categoria_id", "categoria__slug", "categoria__nome", "categoria__cor",
    "marca", "unidade_medida",
    "quantidade_atual", "quantidade_minima", "preco_custo", "preco_venda",
    "validade", "lote", "numero_nota", "dias_alerta_validade",
    "observacoes", "is_active", "created_at", "updated_at",
)


def _produto_values_row(row: dict) -> dict:
    item = dict(row)
    item.setdefault("numero_nota", "")
    item["categoria"] = row.get("categoria_id")
    item["categoria_slug"] = row.get("categoria__slug") or "outro"
    item["categoria_display"] = row.get("categoria__nome") or "Outro"
    item["categoria_cor"] = row.get("categoria__cor") or "#8B3D52"
    item.pop("categoria__slug", None)
    item.pop("categoria__nome", None)
    item.pop("categoria__cor", None)
    item["estoque_baixo"] = row.get("quantidade_atual", 0) <= row.get("quantidade_minima", 0)
    validade = row.get("validade")
    dias_alerta = row.get("dias_alerta_validade") or 90
    if validade:
        from datetime import date, timedelta
        limite = date.today() + timedelta(days=dias_alerta)
        item["validade_proxima"] = validade <= limite
    else:
        item["validade_proxima"] = False
    return item


def _paginate_produtos_values(queryset, request):
    """Lista produtos via .values() usando paginação padrão."""
    return paginate_queryset(
        queryset.values(*_PRODUTO_VALUES_FIELDS),
        request,
        to_representation=_produto_values_row,
    )


def _filtrar_por_categoria(qs, request):
    categoria_id = request.query_params.get("categoria_id")
    categoria = request.query_params.get("categoria")
    if categoria_id:
        try:
            return qs.filter(categoria_id=int(categoria_id))
        except (TypeError, ValueError):
            return qs.none()
    if not categoria:
        return qs
    cat = str(categoria).strip()
    if cat.isdigit():
        return qs.filter(categoria_id=int(cat))
    return qs.filter(categoria__slug=normalizar_slug_categoria(cat))
