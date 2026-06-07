"""Consultas com roteamento explícito ao schema do tenant (evita 404/500 em PDF e documentos)."""
from tenants.middleware import get_current_tenant_db

from .models import Consulta


def get_consulta_for_tenant(consulta_id, *, select_related=None):
    """
    Retorna Consulta no banco/schema correto da loja.
    Usa all_without_filter + using(tenant_db) como em views_documentos.
    """
    tenant_db = get_current_tenant_db()
    qs = Consulta.objects.all_without_filter().filter(pk=consulta_id)
    if tenant_db and tenant_db != 'default':
        qs = qs.using(tenant_db)
    if select_related:
        qs = qs.select_related(*select_related)
    try:
        return qs.get()
    except Consulta.DoesNotExist:
        return None
