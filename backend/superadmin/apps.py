"""
Configuração do app superadmin
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class SuperadminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'superadmin'
    verbose_name = 'Super Admin'
    
    def ready(self):
        """Configuração quando o app está pronto"""
        try:
            # Importar signals para registrá-los
            from . import signals
            logger.info("✅ Superadmin: Signals de limpeza carregados")
        except Exception as e:
            logger.warning(f"⚠️ Superadmin: Erro ao carregar signals: {e}")