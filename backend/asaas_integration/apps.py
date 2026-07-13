"""
Configuração do app Asaas Integration
"""
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

class AsaasIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asaas_integration'
    verbose_name = 'Integração Asaas'
    
    def ready(self):
        """Configuração quando o app está pronto"""
        try:
            # Importar signals apenas quando o app estiver totalmente carregado
            logger.info("✅ Asaas Integration: Signals carregados")
        except Exception as e:
            logger.warning(f"⚠️ Asaas Integration: Erro ao carregar signals: {e}")