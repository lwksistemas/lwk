"""URLs para NFS-e
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NFSeViewSet
from .views_pdf_public import NFSePdfPublicView

router = DefaultRouter()
router.register(r"nfse", NFSeViewSet, basename="nfse")

urlpatterns = [
    path("nfse/documento-pdf/", NFSePdfPublicView.as_view()),
    path("", include(router.urls)),
]
