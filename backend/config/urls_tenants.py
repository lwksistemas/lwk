"""
URLs para schemas de TENANTS (Suporte e Lojas)
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/stores/', include('stores.urls')),
    path('api/products/', include('products.urls')),
    path('api/tickets/', include('tickets.urls')),
    path('api/clinica/', include('clinica_estetica.urls')),
    path('api/crm/', include('crm_vendas.urls')),
    path('api/ecommerce/', include('ecommerce.urls')),
    path('api/restaurante/', include('restaurante.urls')),
    path('api/servicos/', include('servicos.urls')),
]
