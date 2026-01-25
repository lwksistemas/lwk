from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView

def api_root(request):
    """API Root - Informações do sistema"""
    return JsonResponse({
        'sistema': 'LWK Sistemas',
        'versao': '1.0.0',
        'status': 'online',
        'endpoints': {
            'admin': '/admin/',
            'auth': {
                'superadmin_login': '/api/auth/superadmin/login/',
                'suporte_login': '/api/auth/suporte/login/',
                'loja_login': '/api/auth/loja/login/',
                'refresh': '/api/auth/token/refresh/',
                'logout': '/api/auth/logout/',
            },
            'superadmin': '/api/superadmin/',
            'suporte': '/api/suporte/',
            'stores': '/api/stores/',
            'products': '/api/products/',
            'asaas': '/api/asaas/',
            'clinica': '/api/clinica/',
            'crm': '/api/crm/',
            'ecommerce': '/api/ecommerce/',
            'restaurante': '/api/restaurante/',
            'servicos': '/api/servicos/',
        },
        'documentacao': 'Sistema Multi-Tenant para gestão de lojas'
    })

urlpatterns = [
    path('', api_root, name='api_root'),  # Rota raiz
    path('api/', api_root, name='api_info'),  # Informações da API
    path('admin/', admin.site.urls),
    
    # Autenticação JWT SEGURA com isolamento por grupo
    path('api/auth/', include('config.urls_auth')),  # Rotas de autenticação
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # APIs
    path('api/stores/', include('stores.urls')),
    path('api/products/', include('products.urls')),
    path('api/suporte/', include('suporte.urls')),
    path('api/superadmin/', include('superadmin.urls')),  # API Super Admin
    path('api/asaas/', include('asaas_integration.urls')),  # API Asaas
    
    # APIs dos tipos de loja
    path('api/clinica/', include('clinica_estetica.urls')),
    path('api/crm/', include('crm_vendas.urls')),
    path('api/ecommerce/', include('ecommerce.urls')),
    path('api/restaurante/', include('restaurante.urls')),
    path('api/servicos/', include('servicos.urls')),
]
