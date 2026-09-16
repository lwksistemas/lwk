"""Consultas no schema da loja (manager aplica loja_id + using tenant)."""
from .models import Consulta


def get_consulta_for_tenant(consulta_id, *, select_related=None):
    """Retorna Consulta isolada pela loja do request, ou None."""
    qs = Consulta.objects.filter(pk=consulta_id)
    if select_related:
        qs = qs.select_related(*select_related)
    try:
        return qs.get()
    except Consulta.DoesNotExist:
        return None
