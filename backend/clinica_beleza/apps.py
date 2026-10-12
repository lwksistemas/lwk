from django.apps import AppConfig


class ClinicaBelezaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clinica_beleza"
    verbose_name = "Clínica da Beleza"

    def ready(self):
        from nfse_integration.config_loja import TIPOS_CONFIG_CLINICA, registrar_config_nfse_tipos

        def _config_nfse(loja):
            from clinica_beleza.nfse_config_service import get_or_create_nfse_config

            return get_or_create_nfse_config(loja.id)

        registrar_config_nfse_tipos(TIPOS_CONFIG_CLINICA, _config_nfse)
        import clinica_beleza.signals  # noqa: F401
