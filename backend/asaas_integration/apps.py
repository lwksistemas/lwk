"""Configuração do app Asaas Integration
"""
import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AsaasIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "asaas_integration"
    verbose_name = "Integração Asaas"

    def ready(self):
        """Registra signals (import obrigatório — o decorator @receiver só roda no import)."""
        try:
            from . import signals  # noqa: F401

            logger.info("✅ Asaas Integration: Signals carregados")
        except Exception as e:
            logger.warning("⚠️ Asaas Integration: Erro ao carregar signals: %s", e)
