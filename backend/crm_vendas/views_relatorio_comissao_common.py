"""Helpers compartilhados pelas views de relatório de comissão."""
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id


def loja_id_ou_erro():
    loja_id = get_current_loja_id()
    if not loja_id:
        return None, Response({'detail': 'Loja não identificada.'}, status=400)
    return loja_id, None
