"""
URLs para integração com Asaas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
import logging

logger = logging.getLogger(__name__)

# Criar router vazio
router = DefaultRouter()

# Importar views diretamente (sem try/except para permitir que o erro apareça)
from . import views

# URLs para configuração e monitoramento
urlpatterns = [
    # Router URLs (vazio por enquanto)
    path('', include(router.urls)),
    
    # URLs de configuração
    path('config/', views.asaas_config, name='asaas-config'),
    path('test/', views.asaas_test, name='asaas-test'),
    path('status/', views.asaas_status, name='asaas-status'),
    path('stats/', views.asaas_stats, name='asaas-stats'),
    path('sync/', views.asaas_sync, name='asaas-sync'),
    
    # Webhook para receber notificações
    path('webhook/', views.asaas_webhook, name='asaas-webhook'),
]