"""
URLs temporárias sem integração Asaas
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # APIs principais
    path('api/auth/', include('rest_framework.urls')),
    path('api/stores/', include('stores.urls')),
    path('api/products/', include('products.urls')),
    path('api/suporte/', include('suporte.urls')),
    path('api/superadmin/', include('superadmin.urls')),
    
    # Apps específicos por tipo de loja
    path('api/clinica/', include('clinica_estetica.urls')),
    path('api/crm/', include('crm_vendas.urls')),
    path('api/ecommerce/', include('ecommerce.urls')),
    path('api/restaurante/', include('restaurante.urls')),
    path('api/servicos/', include('servicos.urls')),
    
    # Tenants
    path('api/tenants/', include('tenants.urls')),
    
    # API Asaas - TEMPORARIAMENTE DESABILITADA
    # path('api/asaas/', include('asaas_integration.urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)