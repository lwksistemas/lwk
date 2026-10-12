from django.apps import AppConfig


class CrmVendasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crm_vendas"
    verbose_name = "CRM Vendas"

    def ready(self):
        from nfse_integration.config_loja import registrar_config_nfse_padrao

        def _config_nfse(loja):
            from crm_vendas.models import CRMConfig

            return CRMConfig.get_or_create_for_loja(loja.id)

        registrar_config_nfse_padrao(_config_nfse)
        import crm_vendas.signals  # noqa: F401
