from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação JWT
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # APIs
    path('api/stores/', include('stores.urls')),
    path('api/products/', include('products.urls')),
    path('api/suporte/', include('suporte.urls')),
    path('api/superadmin/', include('superadmin.urls')),  # API Super Admin
]
