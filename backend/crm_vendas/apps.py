from django.apps import AppConfig


class CrmVendasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_vendas'
    verbose_name = 'CRM Vendas'

    def ready(self):
        import crm_vendas.signals  # noqa: F401
