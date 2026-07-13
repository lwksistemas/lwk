"""
URLs para integração com Asaas
"""
import logging

from django.urls import include, path
from rest_framework.routers import DefaultRouter

logger = logging.getLogger(__name__)

# Criar router
router = DefaultRouter()

# Importar views diretamente (sem try/except para permitir que o erro apareça)
from . import views
from . import views_nfse_config as nfse_config_views

# Registrar ViewSets
router.register(r'subscriptions', views.AsaasSubscriptionViewSet, basename='asaas-subscriptions')
router.register(r'payments', views.AsaasPaymentViewSet, basename='asaas-payments')

# URLs para configuração e monitoramento
urlpatterns = [
    # Router URLs (ViewSets)
    path('', include(router.urls)),
    
    # URLs de configuração
    path('config/', views.asaas_config, name='asaas-config'),
    path('test/', views.asaas_test, name='asaas-test'),
    path('test-public/', views.asaas_test_public, name='asaas-test-public'),
    path('status/', views.asaas_status, name='asaas-status'),
    path('diagnostico/', views.asaas_diagnostico, name='asaas-diagnostico'),
    path('stats/', views.asaas_stats, name='asaas-stats'),
    path('sync/', views.asaas_sync, name='asaas-sync'),
    path('sync/stats/', views.asaas_sync_stats, name='asaas-sync-stats'),
    path('sync/realtime/', views.asaas_sync_realtime, name='asaas-sync-realtime'),
    
    # Webhook para receber notificações
    path('webhook/', views.asaas_webhook, name='asaas-webhook'),
    
    # URLs de exclusão/limpeza
    path('cleanup/orphans/', views.asaas_cleanup_orphans, name='asaas-cleanup-orphans'),
    path('delete/loja/', views.asaas_delete_loja, name='asaas-delete-loja'),
    
    # NFS-e Config do Superadmin
    path('nfse-config/', nfse_config_views.nfse_config_view, name='nfse-config'),
    path('nfse-config/test-nacional/', nfse_config_views.nfse_config_test_nacional, name='nfse-config-test-nacional'),
]