"""
URLs de Autenticação para Clínica da Beleza
"""
from django.urls import path
from .auth_views import (
    ClinicaLoginView,
    ClinicaTokenRefreshView,
    MeView,
    LogoutView,
    CheckPermissionsView,
    UserListView,
)

app_name = 'clinica_beleza_auth'

urlpatterns = [
    # Autenticação
    path('login/', ClinicaLoginView.as_view(), name='login'),
    path('refresh/', ClinicaTokenRefreshView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Informações do usuário
    path('me/', MeView.as_view(), name='me'),
    path('permissions/', CheckPermissionsView.as_view(), name='permissions'),
    
    # Gerenciamento de usuários (apenas Admin)
    path('users/', UserListView.as_view(), name='users'),
]
