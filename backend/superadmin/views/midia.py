"""Views superadmin para navegação do servidor de mídia."""
from __future__ import annotations

import logging
import re

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.media_storage import (
    MEDIA_SERVER_URL,
    MEDIA_SYSTEM_TENANTS,
    media_list_files,
    media_list_folders,
    media_list_tenants,
    normalize_media_tenant,
)

from ..models import Loja
from .permissions import IsSuperAdmin

logger = logging.getLogger(__name__)

_SYSTEM_LABELS = {
    "superadmin": "Superadmin (sistema)",
    "suporte": "Suporte (sistema)",
}


def _format_doc(tenant: str) -> str:
    digits = re.sub(r"\D", "", tenant or "")
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    if len(digits) == 14:
        return (
            f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/"
            f"{digits[8:12]}-{digits[12:]}"
        )
    return tenant


def _loja_map_by_tenant() -> dict[str, dict]:
    """Mapa tenant (CPF/CNPJ dígitos) → dados da loja."""
    mapping: dict[str, dict] = {}
    for loja in Loja.objects.all().only("id", "nome", "slug", "cpf_cnpj", "is_active"):
        digits = re.sub(r"\D", "", loja.cpf_cnpj or "")
        if len(digits) not in (11, 14):
            continue
        # Preferir loja ativa se houver colisão
        prev = mapping.get(digits)
        if prev and prev.get("is_active") and not loja.is_active:
            continue
        mapping[digits] = {
            "loja_id": loja.id,
            "nome": loja.nome,
            "slug": loja.slug,
            "is_active": loja.is_active,
        }
    return mapping


@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def listar_midia_tenants(request):
    """Lista pastas raiz do servidor de mídia com nome da loja ao lado do CPF/CNPJ."""
    raw = media_list_tenants()
    if raw is None:
        return Response(
            {"error": "Falha ao consultar servidor de mídia"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    loja_map = _loja_map_by_tenant()
    items = []
    for entry in raw.get("tenants") or []:
        tenant = entry.get("tenant") or ""
        if tenant in MEDIA_SYSTEM_TENANTS:
            nome = _SYSTEM_LABELS.get(tenant, tenant)
            loja_id = None
            slug = tenant
            is_active = True
            tipo = "sistema"
        else:
            info = loja_map.get(tenant) or {}
            nome = info.get("nome") or "Loja não cadastrada"
            loja_id = info.get("loja_id")
            slug = info.get("slug")
            is_active = bool(info.get("is_active", False)) if info else False
            tipo = "loja" if info else "orfao"

        items.append({
            "tenant": tenant,
            "documento": _format_doc(tenant) if tenant not in MEDIA_SYSTEM_TENANTS else tenant,
            "nome": nome,
            "loja_id": loja_id,
            "slug": slug,
            "is_active": is_active,
            "tipo": tipo,
            "folders": entry.get("folders") or [],
            "folder_count": entry.get("folder_count") or 0,
        })

    items.sort(key=lambda x: (0 if x["tipo"] == "loja" else 1, (x["nome"] or "").lower()))
    return Response({
        "tenants": items,
        "total": len(items),
        "media_server": MEDIA_SERVER_URL,
    })


@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def listar_midia_pastas(request, tenant: str):
    """Lista pastas (fotos, docs, …) de um tenant."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return Response({"error": "Tenant inválido"}, status=status.HTTP_400_BAD_REQUEST)

    raw = media_list_folders(tenant_key)
    if raw is None:
        return Response(
            {"error": "Falha ao consultar pastas no servidor de mídia"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    loja_map = _loja_map_by_tenant()
    if tenant_key in MEDIA_SYSTEM_TENANTS:
        nome = _SYSTEM_LABELS.get(tenant_key, tenant_key)
    else:
        nome = (loja_map.get(tenant_key) or {}).get("nome") or "Loja não cadastrada"

    return Response({
        "tenant": tenant_key,
        "documento": _format_doc(tenant_key) if tenant_key not in MEDIA_SYSTEM_TENANTS else tenant_key,
        "nome": nome,
        "folders": raw.get("folders") or [],
    })


@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def listar_midia_arquivos(request, tenant: str, folder: str):
    """Lista arquivos de uma pasta do tenant."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return Response({"error": "Tenant inválido"}, status=status.HTTP_400_BAD_REQUEST)

    raw = media_list_files(tenant_key, folder)
    if raw is None:
        return Response(
            {"error": "Falha ao listar arquivos no servidor de mídia"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    base = MEDIA_SERVER_URL.rstrip("/")
    files = []
    for f in raw.get("files") or []:
        rel = f.get("url") or ""
        files.append({
            **f,
            "public_url": f"{base}{rel}" if rel.startswith("/") else rel,
        })

    loja_map = _loja_map_by_tenant()
    if tenant_key in MEDIA_SYSTEM_TENANTS:
        nome = _SYSTEM_LABELS.get(tenant_key, tenant_key)
    else:
        nome = (loja_map.get(tenant_key) or {}).get("nome") or "Loja não cadastrada"

    return Response({
        "tenant": tenant_key,
        "documento": _format_doc(tenant_key) if tenant_key not in MEDIA_SYSTEM_TENANTS else tenant_key,
        "nome": nome,
        "folder": raw.get("folder") or folder,
        "files": files,
        "subfolders": raw.get("subfolders") or [],
        "truncated": bool(raw.get("truncated")),
    })


@api_view(["DELETE"])
@permission_classes([IsSuperAdmin])
def excluir_midia_arquivo(request, tenant: str, folder: str, filename: str):
    """Exclui um arquivo do servidor de mídia."""
    tenant_key = normalize_media_tenant(tenant)
    if not tenant_key:
        return Response({"error": "Tenant inválido"}, status=status.HTTP_400_BAD_REQUEST)

    from core.media_storage import media_delete_tenant

    sucesso = media_delete_tenant(tenant_key, f"{folder}/{filename}")
    if sucesso:
        return Response({"success": True}, status=status.HTTP_200_OK)
    return Response({"error": "Falha ao excluir arquivo"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
