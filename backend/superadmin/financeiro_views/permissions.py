"""Permissões do financeiro das lojas."""
from rest_framework import permissions

from ..models import Loja


class IsLojaOwner(permissions.BasePermission):
    """Permissão para proprietário da loja"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin tem acesso total
        if request.user.is_superuser:
            return True
        
        # Verificar se é proprietário de alguma loja
        return Loja.objects.filter(owner=request.user, is_active=True).exists()
    
    def has_object_permission(self, request, view, obj):
        # Super admin tem acesso total
        if request.user.is_superuser:
            return True
        
        # Verificar se é proprietário da loja específica
        if hasattr(obj, 'loja'):
            return obj.loja.owner == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False
