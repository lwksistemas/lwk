from django.apps import AppConfig


class CabeleireiroConfig(AppConfig):
    """
    Configuração do app Cabeleireiro
    
    Boas práticas:
    - Registro de signals no método ready()
    - Documentação clara
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cabeleireiro'
    verbose_name = 'Cabeleireiro'
    
    def ready(self):
        """
        Método executado quando o app está pronto.
        Registra os signals do app.
        """
        # Import signals para registrá-los
        import cabeleireiro.signals  # noqa: F401
