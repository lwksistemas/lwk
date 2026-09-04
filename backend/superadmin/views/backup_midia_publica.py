"""API pública: listar pastas/arquivos de mídia da loja via token do e-mail de backup."""
from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.media_storage import (
    MEDIA_SERVER_URL,
    _cpf_cnpj_digits,
    media_list_files,
    media_list_folders,
    normalize_media_tenant,
)

from ..backup_midia_link import decodificar_token_backup_midia
from ..models import Loja


def _loja_do_token(token: str):
    payload = decodificar_token_backup_midia(token)
    if not payload:
        return None, Response({"error": "Link inválido ou expirado."}, status=status.HTTP_404_NOT_FOUND)
    try:
        loja = Loja.objects.get(pk=payload["loja_id"])
    except Loja.DoesNotExist:
        return None, Response({"error": "Loja não encontrada."}, status=status.HTTP_404_NOT_FOUND)
    return loja, None


def _tenant_loja(loja) -> str | None:
    return normalize_media_tenant(_cpf_cnpj_digits(loja))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def backup_midia_publica(request, token: str):
    """Lista pastas raiz ou arquivos de uma pasta (query ?folder=)."""
    loja, err = _loja_do_token(token)
    if err:
        return err
    tenant = _tenant_loja(loja)
    if not tenant:
        return Response({
            "loja_nome": loja.nome,
            "folders": [],
            "files": [],
            "subfolders": [],
            "folder": "",
        })

    folder = (request.query_params.get("folder") or "").strip().strip("/")
    base = MEDIA_SERVER_URL.rstrip("/")
    if not folder:
        raw = media_list_folders(tenant) or {}
        return Response({
            "loja_nome": loja.nome,
            "folder": "",
            "folders": raw.get("folders") or [],
            "files": [],
            "subfolders": [],
        })

    raw = media_list_files(tenant, folder) or {}
    files = []
    for item in raw.get("files") or []:
        rel = item.get("url") or ""
        files.append({
            **item,
            "public_url": f"{base}{rel}" if rel.startswith("/") else rel,
        })
    return Response({
        "loja_nome": loja.nome,
        "folder": raw.get("folder") or folder,
        "folders": [],
        "files": files,
        "subfolders": raw.get("subfolders") or [],
        "truncated": bool(raw.get("truncated")),
    })
