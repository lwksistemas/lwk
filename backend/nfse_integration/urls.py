"""
URLs para NFS-e
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NFSeViewSet

router = DefaultRouter()
router.register(r'nfse', NFSeViewSet, basename='nfse')

urlpatterns = [
    path('', include(router.urls)),
]
