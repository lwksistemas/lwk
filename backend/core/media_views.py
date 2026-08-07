"""Views para upload de mídia — proxy para o servidor media.lwksistemas.com.br."""
import re

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.media_storage import media_upload as do_media_upload, media_delete as do_media_delete, is_media_url, _cpf_cnpj_digits
from superadmin.models import Loja
from tenants.middleware import get_current_loja_id


@api_view(["POST"])
@parser_classes([MultiPartParser])
def media_upload(request):
    """Upload de arquivo para o servidor de mídia."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({"error": "Loja não identificada"}, status=status.HTTP_400_BAD_REQUEST)

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return Response({"error": "Loja não encontrada"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES.get("file")
    if not file:
        return Response({"error": "Nenhum arquivo enviado"}, status=status.HTTP_400_BAD_REQUEST)

    folder = request.data.get("folder", "fotos")
    allowed_folders = ("fotos", "docs", "avatars", "recibos", "contratos")
    if folder not in allowed_folders:
        folder = "fotos"

    url = do_media_upload(loja, file.read(), filename=file.name or "upload", folder=folder)

    if url:
        return Response({"success": True, "url": url, "filename": file.name}, status=status.HTTP_201_CREATED)

    return Response({"success": False, "error": "Falha ao enviar arquivo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def media_delete(request):
    """Deleta arquivo do servidor de mídia."""
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({"error": "Loja não identificada"}, status=status.HTTP_400_BAD_REQUEST)

    loja = Loja.objects.using("default").filter(id=loja_id).first()
    if not loja:
        return Response({"error": "Loja não encontrada"}, status=status.HTTP_400_BAD_REQUEST)

    url = request.data.get("url", "")
    if not url or not is_media_url(url):
        return Response({"error": "URL inválida"}, status=status.HTTP_400_BAD_REQUEST)

    cnpj = _cpf_cnpj_digits(loja)
    match = re.search(rf"/files/{cnpj}/(\w+)/(.+)$", url)
    if not match:
        return Response({"error": "Não foi possível identificar o arquivo"}, status=status.HTTP_400_BAD_REQUEST)

    folder, filename = match.group(1), match.group(2)
    success = do_media_delete(loja, filename, folder)

    return Response({"success": success})
