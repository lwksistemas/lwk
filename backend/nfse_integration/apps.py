"""
Configuração do app nfse_integration
"""
from django.apps import AppConfig


class NfseIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nfse_integration'
    verbose_name = 'Integração NFS-e'
