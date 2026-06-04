"""OpenAPI / Swagger — acesso restrito (staff) fora de DEBUG."""
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser


class ProtectedSpectacularAPIView(SpectacularAPIView):
    permission_classes = [IsAdminUser]


class ProtectedSpectacularSwaggerView(SpectacularSwaggerView):
    permission_classes = [IsAdminUser]
