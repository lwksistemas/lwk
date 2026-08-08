"""Paginação padrão para Clínica da Beleza.

Uso nas views:
    from .pagination import paginate_queryset

    def get(self, request):
        qs = Patient.objects.all()
        return paginate_queryset(qs, request, PatientSerializer)

Sempre pagina por padrão (page=1, page_size=50).
Opt-out explícito para catálogos pequenos: ?all=1
"""
from rest_framework.response import Response

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _wants_full_list(request) -> bool:
    raw = (request.query_params.get("all") or "").strip().lower()
    return raw in ("1", "true", "yes")


def paginate_queryset(queryset, request, serializer_class=None, serializer_context=None, *, to_representation=None):
    """Pagina o queryset.

    Resposta paginada:
    {
        "count": 150,
        "page": 1,
        "page_size": 50,
        "total_pages": 3,
        "results": [...]
    }

    Com ?all=1 retorna a lista completa (array) — só para catálogos pequenos.
    """
    def serialize_items(items):
        if to_representation is not None:
            return [to_representation(item) for item in items]
        ctx = serializer_context or {}
        return serializer_class(items, many=True, context=ctx).data

    if _wants_full_list(request):
        return Response(serialize_items(queryset))

    try:
        page = max(1, int(request.query_params.get("page") or 1))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = min(
            MAX_PAGE_SIZE,
            max(1, int(request.query_params.get("page_size") or DEFAULT_PAGE_SIZE)),
        )
    except (ValueError, TypeError):
        page_size = DEFAULT_PAGE_SIZE

    total = queryset.count()
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * page_size

    items = queryset[offset:offset + page_size]
    return Response({
        "count": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "results": serialize_items(items),
    })
