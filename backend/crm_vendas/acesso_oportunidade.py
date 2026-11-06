"""Confere se a oportunidade é do vendedor logado.

Dono e administrador usam qualquer oportunidade da loja.
"""
from .utils import get_current_vendedor_id, usuario_administra_crm


def oportunidade_do_usuario(request, oportunidade_id) -> bool:
    if oportunidade_id in (None, ""):
        return False
    try:
        oid = int(getattr(oportunidade_id, "id", oportunidade_id))
    except (TypeError, ValueError):
        return False
    from .models import Oportunidade

    if usuario_administra_crm(request):
        return Oportunidade.objects.filter(pk=oid).exists()
    vid = get_current_vendedor_id(request)
    if not vid:
        return False
    return Oportunidade.objects.filter(pk=oid, vendedor_id=vid).exists()
