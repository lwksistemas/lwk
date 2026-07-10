"""
CRM: personalização da tela de login e identidade visual.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .mixins import CRMPermissionMixin
from .decorators import require_admin_access
from .utils import get_loja_from_context


def _serialize_login_config(loja) -> dict:
    tipo = getattr(loja, 'tipo_loja', None)
    cor_default = getattr(tipo, 'cor_primaria', None) if tipo else None
    cor_primaria = (loja.cor_primaria or '').strip() or cor_default or '#10B981'
    cor_secundaria = (loja.cor_secundaria or '').strip() or '#059669'
    return {
        'logo': (loja.logo or '').strip(),
        'login_background': (loja.login_background or '').strip(),
        'login_logo': (loja.login_logo or '').strip(),
        'cor_primaria': cor_primaria,
        'cor_secundaria': cor_secundaria,
        'agenda_status_colors': getattr(loja, 'agenda_status_colors', None) or {},
    }


class LoginConfigView(CRMPermissionMixin, APIView):
    """
    GET /crm-vendas/login-config/  → logo, cores, agenda_status_colors
    PATCH /crm-vendas/login-config/ → atualiza personalização
    """
    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def get(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(_serialize_login_config(loja))

    @require_admin_access()
    def patch(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        from superadmin.cloudinary_utils import delete_cloudinary_image
        from superadmin.loja_utils import invalidate_loja_info_publica_cache
        from superadmin.theme_colors import sanitize_agenda_status_colors

        update_fields = ['updated_at']
        loja_slug = loja.slug

        if 'logo' in request.data:
            val = (request.data.get('logo') or '').strip()
            old_logo = (loja.logo or '').strip()
            if old_logo and old_logo != val and 'cloudinary.com' in old_logo:
                delete_cloudinary_image(old_logo, loja_slug)
            loja.logo = val[:200] if val else ''
            update_fields.append('logo')

        if 'login_background' in request.data:
            val = (request.data.get('login_background') or '').strip()
            old_background = (loja.login_background or '').strip()
            if old_background and old_background != val and 'cloudinary.com' in old_background:
                delete_cloudinary_image(old_background, loja_slug)
            loja.login_background = val[:200] if val else ''
            update_fields.append('login_background')

        if 'login_logo' in request.data:
            val = (request.data.get('login_logo') or '').strip()
            old_login_logo = (loja.login_logo or '').strip()
            if old_login_logo and old_login_logo != val and 'cloudinary.com' in old_login_logo:
                delete_cloudinary_image(old_login_logo, loja_slug)
            loja.login_logo = val[:200] if val else ''
            update_fields.append('login_logo')

        if 'cor_primaria' in request.data:
            val = (request.data.get('cor_primaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_primaria = val[:7]
                update_fields.append('cor_primaria')
        if 'cor_secundaria' in request.data:
            val = (request.data.get('cor_secundaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_secundaria = val[:7]
                update_fields.append('cor_secundaria')

        if 'agenda_status_colors' in request.data:
            loja.agenda_status_colors = sanitize_agenda_status_colors(
                request.data.get('agenda_status_colors')
            )
            update_fields.append('agenda_status_colors')

        loja.save(update_fields=update_fields)
        invalidate_loja_info_publica_cache(loja)

        return Response(_serialize_login_config(loja))
