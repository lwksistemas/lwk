"""
Permissões para API Clínica da Beleza.
Recepção: apenas admin (owner) ou usuário com perfil recepção.
"""
from rest_framework.permissions import BasePermission


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

        from .views_base import resolve_loja_id_from_request
        from superadmin.models import Loja, ProfissionalUsuario

        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return False

        try:
            loja = Loja.objects.get(pk=loja_id)
        except Loja.DoesNotExist:
            return False

        if loja.owner_id == request.user.id:
            return True

        return ProfissionalUsuario.objects.filter(
            user=request.user,
            loja=loja,
            perfil__in=(
                ProfissionalUsuario.PERFIL_ADMINISTRADOR,
                ProfissionalUsuario.PERFIL_RECEPCAO,
                ProfissionalUsuario.PERFIL_RECEPCIONISTA,
            ),
        ).exists()
