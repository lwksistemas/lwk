"""
Permissões para API Clínica da Beleza.
Recepção: apenas admin (owner) ou usuário com perfil recepção.
"""
from rest_framework.permissions import BasePermission


def _get_loja_from_request(request):
    """Obtém a loja a partir dos headers X-Loja-ID ou X-Tenant-Slug (schema public)."""
    loja_id = request.headers.get("X-Loja-ID")
    slug = request.headers.get("X-Tenant-Slug")
    if not request.user.is_authenticated:
        return None
    from superadmin.models import Loja
    if loja_id:
        try:
            return Loja.objects.filter(pk=int(loja_id)).first()
        except (ValueError, TypeError):
            pass
    if slug:
        return Loja.objects.filter(slug__iexact=slug.strip()).first()
    return None


class IsRecepcaoOrAdmin(BasePermission):
    """
    Permite acesso à agenda e áreas de recepção:
    - Dono da loja (owner)
    - ProfissionalUsuario com perfil administrador, recepcionista ou recepcao (legado)
    """
    message = "Acesso permitido apenas para administrador ou perfil recepção."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        loja = _get_loja_from_request(request)
        if not loja:
            return False
        if loja.owner_id == request.user.id:
            return True
        from superadmin.models import ProfissionalUsuario
        return ProfissionalUsuario.objects.filter(
            user=request.user,
            loja=loja,
            perfil__in=(
                ProfissionalUsuario.PERFIL_ADMINISTRADOR,
                ProfissionalUsuario.PERFIL_RECEPCAO,
                ProfissionalUsuario.PERFIL_RECEPCIONISTA,
            ),
        ).exists()
