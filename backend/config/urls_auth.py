"""
URLs de autenticação para todos os tipos de usuário
"""
from django.urls import path
from superadmin.auth_views_secure import SecureLoginView, SecureLogoutView, BeaconLogoutView

urlpatterns = [
    # Login por tipo de usuário
    path('superadmin/login/', SecureLoginView.as_view(), {'user_type': 'superadmin'}, name='superadmin-login'),
    path('suporte/login/', SecureLoginView.as_view(), {'user_type': 'suporte'}, name='suporte-login'),
    path('loja/login/', SecureLoginView.as_view(), {'user_type': 'loja'}, name='loja-login'),
    
    # Logout (comum para todos)
    path('logout/', SecureLogoutView.as_view(), name='logout'),
    
    # Logout via beacon (ao fechar aba do navegador)
    path('logout/beacon/', BeaconLogoutView.as_view(), name='logout-beacon'),
]
