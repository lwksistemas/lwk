"""
URLs para integração com Asaas
Carregamento condicional para evitar problemas com requests na inicialização
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
import logging

logger = logging.getLogger(__name__)

# Tentar carregar as views, se falhar, criar router vazio
try:
    from .views import AsaasCustomerViewSet, AsaasPaymentViewSet, LojaAssinaturaViewSet
    
    router = DefaultRouter()
    router.register(r'customers', AsaasCustomerViewSet)
    router.register(r'payments', AsaasPaymentViewSet)
    router.register(r'subscriptions', LojaAssinaturaViewSet)
    
    logger.info("✅ Asaas Integration: Views carregadas com sucesso")
    
except ImportError as e:
    # Se requests não estiver disponível, criar router vazio
    logger.warning(f"⚠️ Asaas Integration: Views não disponíveis durante inicialização: {e}")
    router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]