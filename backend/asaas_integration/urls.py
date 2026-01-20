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
    from . import views
    
    router = DefaultRouter()
    # router.register(r'customers', views.AsaasCustomerViewSet)
    # router.register(r'payments', views.AsaasPaymentViewSet)
    # router.register(r'subscriptions', views.LojaAssinaturaViewSet)
    
    # URLs para configuração e monitoramento
    config_urls = [
        path('config/', views.asaas_config, name='asaas-config'),
        path('test/', views.asaas_test, name='asaas-test'),
        path('status/', views.asaas_status, name='asaas-status'),
        path('stats/', views.asaas_stats, name='asaas-stats'),
        path('sync/', views.asaas_sync, name='asaas-sync'),
    ]
    
    logger.info("✅ Asaas Integration: Views carregadas com sucesso")
    
except ImportError as e:
    # Se requests não estiver disponível, criar router vazio
    logger.warning(f"⚠️ Asaas Integration: Views não disponíveis durante inicialização: {e}")
    router = DefaultRouter()
    config_urls = []

urlpatterns = [
    path('', include(router.urls)),
] + config_urls