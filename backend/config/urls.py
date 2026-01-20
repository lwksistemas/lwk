from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def api_root(request):
    """API Root - Informações do sistema"""
    return JsonResponse({
        'sistema': 'LWK Sistemas',
        'versao': '1.0.0',
        'status': 'online',
        'endpoints': {
            'admin': '/admin/',
            'auth': {
                'token': '/api/auth/token/',
                'refresh': '/api/auth/token/refresh/',
            },
            'superadmin': '/api/superadmin/',
            'suporte': '/api/suporte/',
            'stores': '/api/stores/',
            'products': '/api/products/',
            'asaas': '/api/asaas/',
        },
        'documentacao': 'Sistema Multi-Tenant para gestão de lojas'
    })

urlpatterns = [
    path('', api_root, name='api_root'),  # Rota raiz
    path('api/', api_root, name='api_info'),  # Informações da API
    path('admin/', admin.site.urls),
    
    # Autenticação JWT
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # APIs
    path('api/stores/', include('stores.urls')),
    path('api/products/', include('products.urls')),
    path('api/suporte/', include('suporte.urls')),
    path('api/superadmin/', include('superadmin.urls')),  # API Super Admin
    path('api/asaas/', include('asaas_integration.urls')),  # API Asaas
]
