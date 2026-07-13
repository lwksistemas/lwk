"""Permissões reutilizáveis para o sistema.
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permissão APENAS para super admins.

    Uso:
        permission_classes = [IsSuperAdmin]
    """

    message = "Apenas super administradores podem acessar este recurso."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser and
            request.user.is_active
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user and
            request.user.is_superuser and
            request.user.is_active
        )


class HasLojaAccess(permissions.BasePermission):
    """Exige que o usuário autenticado tenha vínculo com a loja do contexto (headers).
    Superuser passa. Endpoints sem headers de loja são negados para usuários de loja.
    """

    message = "Você não tem permissão para acessar esta loja."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        from core.tenant_access import resolve_lojas_from_request, user_can_access_loja
        from superadmin.models import Loja
        from tenants.middleware import ensure_loja_context, get_current_loja_id

        for loja in resolve_lojas_from_request(request):
            if not user_can_access_loja(request.user, loja):
                return False

        ensure_loja_context(request)
        loja_id = get_current_loja_id()
        if not loja_id:
            return False

        loja = Loja.objects.filter(id=loja_id).first()
        return user_can_access_loja(request.user, loja) if loja else False


class IsSuperAdminOrReadOnly(permissions.BasePermission):
    """Permissão para leitura pública, mas apenas super admin pode editar.

    Uso:
        permission_classes = [IsSuperAdminOrReadOnly]
    """

    def has_permission(self, request, view):
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escrita apenas para super admin
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser and
            request.user.is_active
        )

    def has_object_permission(self, request, view, obj):
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True

        # Escrita apenas para super admin
        return (
            request.user and
            request.user.is_superuser and
            request.user.is_active
        )
