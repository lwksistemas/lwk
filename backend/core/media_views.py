"""Views para upload de mídia — proxy para o servidor media.lwksistemas.com.br."""
from types import SimpleNamespace

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.media_storage import (
    MEDIA_TENANT_SUPERADMIN,
    MEDIA_TENANT_SUPORTE,
    media_upload_tenant,
    media_delete_tenant,
    is_media_url,
    parse_media_url,
    _cpf_cnpj_digits,
    normalize_media_tenant,
)
from superadmin.models import Loja
from tenants.middleware import get_current_loja_id


def _is_suporte_user(user) -> bool:
    if not user or not user.is_authenticated or not user.is_active:
        return False
    try:
        from superadmin.models import UsuarioSistema

        return UsuarioSistema.objects.using("default").filter(
            user=user,
            tipo="suporte",
            is_active=True,
        ).exists()
    except Exception:
        return False


def _system_tenant_namespace(tenant_key: str) -> SimpleNamespace:
    return SimpleNamespace(
        cpf_cnpj="",
        slug=tenant_key,
        media_tenant=tenant_key,
        id=0,
    )


def _resolve_media_tenant(request):
    """Resolve a chave de tenant do storage.

    Prioridade:
      1. Loja no contexto → CPF/CNPJ da loja
      2. Superuser → superadmin
      3. UsuarioSistema suporte → suporte
    """
    loja_id = get_current_loja_id()
    if loja_id:
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja:
            return None, Response({"error": "Loja não encontrada"}, status=status.HTTP_400_BAD_REQUEST)
        tenant = normalize_media_tenant(_cpf_cnpj_digits(loja))
        if not tenant:
            return None, Response(
                {"error": "Loja sem CPF/CNPJ válido para armazenamento"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return tenant, None

    user = getattr(request, "user", None)
    if user and user.is_authenticated and user.is_superuser and user.is_active:
        return MEDIA_TENANT_SUPERADMIN, None

    if _is_suporte_user(user):
        return MEDIA_TENANT_SUPORTE, None

    return None, Response({"error": "Loja não identificada"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@parser_classes([MultiPartParser])
def media_upload(request):
    """Upload de arquivo para o servidor de mídia."""
    tenant, error = _resolve_media_tenant(request)
    if error:
        return error

    file = request.FILES.get("file")
    if not file:
        return Response({"error": "Nenhum arquivo enviado"}, status=status.HTTP_400_BAD_REQUEST)

    folder = request.data.get("folder", "fotos")
    allowed_folders = ("fotos", "docs", "avatars", "recibos", "contratos")
    if folder not in allowed_folders:
        folder = "fotos"

    url = media_upload_tenant(tenant, file.read(), filename=file.name or "upload", folder=folder)

    if url:
        return Response(
            {"success": True, "url": url, "filename": file.name, "tenant": tenant},
            status=status.HTTP_201_CREATED,
        )

    return Response({"success": False, "error": "Falha ao enviar arquivo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def media_delete(request):
    """Deleta arquivo do servidor de mídia."""
    tenant, error = _resolve_media_tenant(request)
    if error:
        return error

    url = request.data.get("url", "")
    if not url or not is_media_url(url):
        return Response({"error": "URL inválida"}, status=status.HTTP_400_BAD_REQUEST)

    parsed = parse_media_url(url)
    if not parsed:
        return Response({"error": "Não foi possível identificar o arquivo"}, status=status.HTTP_400_BAD_REQUEST)

    url_tenant, folder, filename = parsed
    if url_tenant != tenant:
        return Response({"error": "Arquivo fora da pasta autorizada"}, status=status.HTTP_403_FORBIDDEN)

    success = media_delete_tenant(tenant, filename, folder)
    return Response({"success": success})
