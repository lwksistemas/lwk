"""
Permissões reutilizáveis para o sistema.
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permissão APENAS para super admins.
    
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


class IsSuperAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão para leitura pública, mas apenas super admin pode editar.
    
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
