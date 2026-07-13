"""CRM: personalização da tela de login e identidade visual.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .decorators import require_admin_access
from .mixins import CRMPermissionMixin
from .utils import get_loja_from_context


def _patch_imagem_loja(loja, field, data, loja_slug, delete_fn):
    """Atualiza campo de imagem na loja, deletando a imagem antiga do Cloudinary se necessário."""
    if field not in data:
        return False
    val = (data.get(field) or "").strip()
    old_val = (getattr(loja, field) or "").strip()
    if old_val and old_val != val and "cloudinary.com" in old_val:
        delete_fn(old_val, loja_slug)
    setattr(loja, field, val[:200] if val else "")
    return True


def _patch_cor_loja(loja, field, data):
    """Atualiza campo de cor hex simples (#RRGGBB) na loja."""
    if field not in data:
        return False
    val = (data.get(field) or "").strip()
    if val and val.startswith("#") and len(val) <= 7:
        setattr(loja, field, val[:7])
        return True
    return False


def _serialize_login_config(loja) -> dict:
    tipo = getattr(loja, "tipo_loja", None)
    cor_default = getattr(tipo, "cor_primaria", None) if tipo else None
    cor_primaria = (loja.cor_primaria or "").strip() or cor_default or "#10B981"
    cor_secundaria = (loja.cor_secundaria or "").strip() or "#059669"
    return {
        "logo": (loja.logo or "").strip(),
        "login_background": (loja.login_background or "").strip(),
        "login_logo": (loja.login_logo or "").strip(),
        "cor_primaria": cor_primaria,
        "cor_secundaria": cor_secundaria,
        "cor_fundo_pagina": (getattr(loja, "cor_fundo_pagina", None) or "").strip(),
        "agenda_status_colors": getattr(loja, "agenda_status_colors", None) or {},
        "colunas_consultas": getattr(loja, "colunas_consultas", None) or [],
        "colunas_estoque": getattr(loja, "colunas_estoque", None) or [],
    }


class LoginConfigView(CRMPermissionMixin, APIView):
    """GET /crm-vendas/login-config/  → logo, cores, agenda_status_colors
    PATCH /crm-vendas/login-config/ → atualiza personalização
    """

    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def get(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {"error": "Contexto de loja não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_serialize_login_config(loja))

    @require_admin_access()
    def patch(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {"error": "Contexto de loja não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        from superadmin.cloudinary_utils import delete_cloudinary_image
        from superadmin.loja_utils import invalidate_loja_info_publica_cache
        from superadmin.theme_colors import (
            normalize_hex_color,
            sanitize_agenda_status_colors,
            sanitize_colunas_consultas,
            sanitize_colunas_estoque,
        )

        update_fields = ["updated_at"]
        loja_slug = loja.slug
        data = request.data

        for img_field in ("logo", "login_background", "login_logo"):
            if _patch_imagem_loja(loja, img_field, data, loja_slug, delete_cloudinary_image):
                update_fields.append(img_field)

        for cor_field in ("cor_primaria", "cor_secundaria"):
            if _patch_cor_loja(loja, cor_field, data):
                update_fields.append(cor_field)

        if "cor_fundo_pagina" in data:
            raw = data.get("cor_fundo_pagina")
            if raw is None or str(raw).strip() == "":
                loja.cor_fundo_pagina = ""
            else:
                loja.cor_fundo_pagina = normalize_hex_color(raw) or loja.cor_fundo_pagina
            update_fields.append("cor_fundo_pagina")

        if "agenda_status_colors" in data:
            loja.agenda_status_colors = sanitize_agenda_status_colors(data.get("agenda_status_colors"))
            update_fields.append("agenda_status_colors")
        if "colunas_consultas" in data:
            loja.colunas_consultas = sanitize_colunas_consultas(data.get("colunas_consultas"))
            update_fields.append("colunas_consultas")
        if "colunas_estoque" in data:
            loja.colunas_estoque = sanitize_colunas_estoque(data.get("colunas_estoque"))
            update_fields.append("colunas_estoque")

        loja.save(update_fields=update_fields)
        invalidate_loja_info_publica_cache(loja)

        # Reconstrói cache imediatamente para que o reload do frontend
        # pegue as cores novas sem precisar esperar cache miss + DB query.
        from superadmin.loja_utils import rebuild_loja_info_publica_cache
        rebuild_loja_info_publica_cache(loja)

        return Response(_serialize_login_config(loja))
