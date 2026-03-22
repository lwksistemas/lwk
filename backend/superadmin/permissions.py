"""
Permissões customizadas para o SuperAdmin
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permissão APENAS para super admins - SEGURANÇA CRÍTICA"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser and request.user.is_active
