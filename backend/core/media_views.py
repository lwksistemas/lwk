"""Views para upload de mídia — proxy para o servidor media.lwksistemas.com.br."""
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.media_storage import media_upload
from tenants.middleware import get_current_loja


@api_view(["POST"])
@parser_classes([MultiPartParser])
def media_upload(request):
    """Upload de arquivo para o servidor de mídia.

    POST /api/media/upload/
    Body (multipart/form-data):
        - file: arquivo
        - folder: subpasta (fotos, docs, avatars, recibos, contratos)
    """
    loja = get_current_loja()
    if not loja:
        return Response(
            {"error": "Loja não identificada"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file = request.FILES.get("file")
    if not file:
        return Response(
            {"error": "Nenhum arquivo enviado"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    folder = request.data.get("folder", "fotos")
    allowed_folders = ("fotos", "docs", "avatars", "recibos", "contratos")
    if folder not in allowed_folders:
        folder = "fotos"

    url = media_upload(
        loja,
        file.read(),
        filename=file.name or "upload",
        folder=folder,
    )

    if url:
        return Response(
            {"success": True, "url": url, "filename": file.name},
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"success": False, "error": "Falha ao enviar arquivo"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@api_view(["POST"])
def media_delete(request):
    """Deleta arquivo do servidor de mídia.

    POST /api/media/delete/
    Body (JSON): { "url": "https://media.lwksistemas.com.br/files/..." }
    """
    from core.media_storage import is_media_url

    loja = get_current_loja()
    if not loja:
        return Response(
            {"error": "Loja não identificada"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    url = request.data.get("url", "")
    if not url or not is_media_url(url):
        return Response(
            {"error": "URL inválida"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Extrair filename do path
    import re
    from core.media_storage import media_delete as _media_delete, _cpf_cnpj_digits

    cnpj = _cpf_cnpj_digits(loja)
    # URL: https://media.../files/{cnpj}/{folder}/{filename}
    match = re.search(rf"/files/{cnpj}/(\w+)/(.+)$", url)
    if not match:
        return Response({"error": "Não foi possível identificar o arquivo"}, status=400)

    folder, filename = match.group(1), match.group(2)
    success = _media_delete(loja, filename, folder)

    return Response({"success": success})
