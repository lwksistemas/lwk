"""Acesso do CRM: só lojas do tipo crm-vendas."""
from rest_framework.permissions import BasePermission

from superadmin.models import Loja

def loja_e_crm(loja) -> bool:
    from superadmin.services.database_schema_service import tipo_usa_app

    tipo = getattr(loja, "tipo_loja", None)
    slug = ((getattr(tipo, "slug", None) or "")).strip().lower()
    return tipo_usa_app(slug, "crm_vendas")


class IsCrmTipoLoja(BasePermission):
    """Bloqueia clínica/salão (e outros tipos) nas rotas /api/crm-vendas/.

    Sem loja no contexto ou loja inexistente: não interfere (a view responde 400).
    Só nega quando a loja existe e o tipo não é CRM.
    """

    message = "Acesso permitido apenas a lojas do tipo CRM Vendas."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        cache = "_crm_tipo_loja_ok"
        if hasattr(request, cache):
            return bool(getattr(request, cache))

        from core.loja_request import resolve_loja_id_from_request
        from tenants.middleware import get_current_loja_id

        loja_id = resolve_loja_id_from_request(request) or get_current_loja_id()
        if not loja_id:
            setattr(request, cache, True)
            return True

        loja = Loja.objects.select_related("tipo_loja").filter(pk=loja_id).first()
        if loja is None:
            setattr(request, cache, True)
            return True

        ok = loja_e_crm(loja)
        setattr(request, cache, ok)
        return ok
