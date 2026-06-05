"""
Paginação padrão para Clínica da Beleza.

Uso nas views:
    from .pagination import paginate_queryset

    def get(self, request):
        qs = Patient.objects.all()
        return paginate_queryset(qs, request, PatientSerializer)

Retrocompatível: se o frontend não enviar ?page=, retorna tudo (sem quebrar apps existentes).
O frontend opta por paginar enviando ?page=1&page_size=20.
"""
from rest_framework.response import Response


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def paginate_queryset(queryset, request, serializer_class=None, serializer_context=None, *, to_representation=None):
    """
    Pagina o queryset SE o frontend enviar ?page=N.
    Sem ?page → retorna lista completa (retrocompatível).

    Resposta paginada:
    {
        "count": 150,
        "page": 1,
        "page_size": 50,
        "total_pages": 3,
        "results": [...]
    }
    """
    def serialize_items(items):
        if to_representation is not None:
            return [to_representation(item) for item in items]
        ctx = serializer_context or {}
        return serializer_class(items, many=True, context=ctx).data

    page_param = request.query_params.get('page')
    if page_param is None:
        return Response(serialize_items(queryset))

    try:
        page = max(1, int(page_param))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))))
    except (ValueError, TypeError):
        page_size = DEFAULT_PAGE_SIZE

    total = queryset.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    items = queryset[offset:offset + page_size]
    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': serialize_items(items),
    })
