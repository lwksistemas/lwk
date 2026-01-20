"""
URLs para integração com Asaas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AsaasCustomerViewSet, AsaasPaymentViewSet, LojaAssinaturaViewSet

router = DefaultRouter()
router.register(r'customers', AsaasCustomerViewSet)
router.register(r'payments', AsaasPaymentViewSet)
router.register(r'subscriptions', LojaAssinaturaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]