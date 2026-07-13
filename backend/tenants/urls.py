from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClientViewSet, create_tenant

router = DefaultRouter()
router.register(r"", ClientViewSet, basename="client")

urlpatterns = [
    path("create/", create_tenant, name="create_tenant"),
    path("", include(router.urls)),
]
