"""PATCH de telefone/e-mail de contato da loja (recibo)."""
from rest_framework import status
from rest_framework.response import Response

from tenants.middleware import get_current_loja_id

from .utils import LojaContextHelper


def patch_contato_loja(request) -> Response:
    """Atualiza telefone_contato / email_contato da loja do contexto."""
    from core.phone_utils import telefone_internacional_br
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(
            {"error": "Contexto de loja não encontrado"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        loja = Loja.objects.using("default").select_related("owner").get(id=loja_id)
    except Loja.DoesNotExist:
        return Response({"error": "Loja não encontrada"}, status=status.HTTP_404_NOT_FOUND)

    data = request.data or {}
    update_fields = ["updated_at"]

    if "telefone_contato" in data:
        raw = data.get("telefone_contato")
        if raw is None or str(raw).strip() == "":
            loja.telefone_contato = ""
        else:
            loja.telefone_contato = (telefone_internacional_br(str(raw).strip()) or str(raw).strip())[:20]
        update_fields.append("telefone_contato")

    if "email_contato" in data:
        raw = data.get("email_contato")
        if raw is None or str(raw).strip() == "":
            loja.email_contato = ""
        else:
            loja.email_contato = str(raw).strip()[:254]
        update_fields.append("email_contato")

    if len(update_fields) > 1:
        loja.save(update_fields=update_fields)
        LojaContextHelper.invalidate_cache(loja_id)

    info = LojaContextHelper.get_loja_owner_info()
    if info is None:
        return Response(
            {"error": "Contexto de loja não encontrado"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(info)
