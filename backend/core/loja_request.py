"""Resolve o loja_id da requisição (headers X-Loja-ID / X-Tenant-Slug). Compartilhado entre apps."""


def _loja_id_se_usuario_pode(request, loja):
    """Header só vale com usuário autenticado e vínculo na loja (JWT já passou)."""
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False) or not loja:
        return None
    from core.tenant_access import user_can_access_loja

    if not user_can_access_loja(user, loja):
        return None
    return loja.id


def resolve_loja_id_from_request(request):
    """Resolve o loja_id a partir dos headers X-Loja-ID ou X-Tenant-Slug.
    Centraliza a lógica que antes estava duplicada em 3+ lugares.
    Fallback de header: só se o usuário autenticado puder acessar a loja.
    Retorna int ou None.
    """
    from tenants.middleware import get_current_loja_id

    loja_id = get_current_loja_id()
    if loja_id:
        return loja_id

    from superadmin.models import Loja

    try:
        lid = request.headers.get("X-Loja-ID")
        if lid:
            loja = Loja.objects.using("default").filter(id=int(lid)).first()
            resolved = _loja_id_se_usuario_pode(request, loja)
            if resolved is not None:
                return resolved
    except (ValueError, TypeError):
        pass

    slug = (request.headers.get("X-Tenant-Slug") or "").strip()
    if slug:
        loja = Loja.objects.using("default").filter(slug__iexact=slug).first()
        return _loja_id_se_usuario_pode(request, loja)

    return None
