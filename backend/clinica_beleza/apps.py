from django.apps import AppConfig


class ClinicaBelezaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clinica_beleza"
    verbose_name = "Clínica da Beleza"

    def ready(self):
        from core.media_views import registrar_buscador_paciente_midia
        from nfse_integration.config_loja import TIPOS_CONFIG_CLINICA, registrar_config_nfse_tipos

        def _config_nfse(loja):
            from clinica_beleza.nfse_config_service import get_or_create_nfse_config

            return get_or_create_nfse_config(loja.id)

        def _paciente_por_id(pk):
            from clinica_beleza.models import Patient

            return Patient.objects.filter(pk=pk).first()

        def _paciente_por_cpf(candidatos):
            from clinica_beleza.models import Patient

            return Patient.objects.filter(cpf__in=candidatos).first()

        registrar_config_nfse_tipos(TIPOS_CONFIG_CLINICA, _config_nfse)
        registrar_buscador_paciente_midia(por_id=_paciente_por_id, por_cpf=_paciente_por_cpf)
        import clinica_beleza.signals  # noqa: F401
