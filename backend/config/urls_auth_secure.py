"""
URLs de Autenticação Seguras com Isolamento por Grupo
"""
from django.urls import path
from superadmin.auth_views_secure import SecureLoginView, SecureLogoutView

urlpatterns = [
    # Login separado por grupo
    path('superadmin/login/', SecureLoginView.as_view(), {'user_type': 'superadmin'}, name='superadmin-login'),
    path('suporte/login/', SecureLoginView.as_view(), {'user_type': 'suporte'}, name='suporte-login'),
    path('loja/login/', SecureLoginView.as_view(), {'user_type': 'loja'}, name='loja-login'),
    
    # Logout universal
    path('logout/', SecureLogoutView.as_view(), name='logout'),
    
    # Endpoint genérico (para compatibilidade, mas com validação)
    path('token/', SecureLoginView.as_view(), name='token_obtain_pair'),
]
