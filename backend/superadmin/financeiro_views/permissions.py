"""Permissões do financeiro das lojas."""
from rest_framework import permissions

from core.tenant_access import loja_ids_where_user_is_admin, user_is_loja_admin


class IsLojaOwner(permissions.BasePermission):
    """Owner, superuser ou administrador da loja (perfil administrador)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return bool(loja_ids_where_user_is_admin(request.user))

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        loja = getattr(obj, "loja", None) or (obj if hasattr(obj, "owner_id") else None)
        return user_is_loja_admin(request.user, loja)
