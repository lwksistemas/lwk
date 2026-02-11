"""
Permissões customizadas para Clínica da Beleza
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permissão apenas para Administradores
    """
    message = "Apenas administradores têm acesso a esta funcionalidade."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo') and
            request.user.cargo == 'admin'
        )


class IsRecepcao(BasePermission):
    """
    Permissão para Recepção e Administradores
    """
    message = "Apenas recepção e administradores têm acesso a esta funcionalidade."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo') and
            request.user.cargo in ['admin', 'recepcao']
        )


class IsProfissional(BasePermission):
    """
    Permissão apenas para Profissionais
    """
    message = "Apenas profissionais têm acesso a esta funcionalidade."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo') and
            request.user.cargo == 'profissional'
        )


class IsAdminOrRecepcao(BasePermission):
    """
    Permissão para Admin ou Recepção
    Alias para IsRecepcao (mais semântico)
    """
    message = "Apenas administradores ou recepção têm acesso."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo') and
            request.user.cargo in ['admin', 'recepcao']
        )


class CanManageAppointments(BasePermission):
    """
    Permissão para gerenciar agendamentos
    Admin e Recepção podem gerenciar todos
    Profissional pode ver apenas os seus
    """
    message = "Você não tem permissão para gerenciar agendamentos."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo')
        )
    
    def has_object_permission(self, request, view, obj):
        # Admin e Recepção podem tudo
        if request.user.cargo in ['admin', 'recepcao']:
            return True
        
        # Profissional pode ver apenas seus agendamentos
        if request.user.cargo == 'profissional':
            return obj.professional == request.user.professional
        
        return False


class CanViewFinancial(BasePermission):
    """
    Permissão para ver informações financeiras
    Apenas Admin
    """
    message = "Apenas administradores podem acessar informações financeiras."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo') and
            request.user.cargo == 'admin'
        )


class CanManageUsers(BasePermission):
    """
    Permissão para gerenciar usuários
    Apenas Admin
    """
    message = "Apenas administradores podem gerenciar usuários."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'cargo') and
            request.user.cargo == 'admin'
        )
