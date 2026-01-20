"""
Configuração do app de integração com Asaas
"""
from django.apps import AppConfig

class AsaasIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asaas_integration'
    verbose_name = 'Integração Asaas'
    
    def ready(self):
        """Importa os signals quando o app estiver pronto"""
        import asaas_integration.signals