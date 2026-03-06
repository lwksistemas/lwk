"""
Comando para executar a verificação de backups automáticos agendados.

Chama executar_backups_automaticos(): para cada loja com backup automático ativo,
verifica se está no horário e se ainda não rodou hoje; se sim, processa o backup
e envia por email para o owner da loja.

Para o backup chegar no email do admin:
  - Agende no Heroku Scheduler para rodar a cada hora (ex.: às :00).
  - Configure no Heroku as variáveis de email: EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
    (ex.: Gmail com senha de app).
  - O horário configurado na tela é interpretado no fuso do servidor (America/Sao_Paulo).

Exemplo Heroku Scheduler:
  Comando: cd backend && python manage.py executar_backups_automaticos
  Frequência: a cada hora
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        'Verifica backups automáticos agendados e processa os que estão no horário. '
        'Agende no Heroku Scheduler a cada hora para que o backup por email funcione.'
    )

    def handle(self, *args, **options):
        from superadmin.tasks import executar_backups_automaticos

        self.stdout.write(
            self.style.SUCCESS(f'=== Verificação de backups automáticos em {timezone.localtime(timezone.now())} ===')
        )

        result = executar_backups_automaticos()

        self.stdout.write(
            self.style.SUCCESS(
                f"Verificação concluída: {result['total_agendados']} backup(s) agendado(s) "
                f"(configurações verificadas: {result['total_verificados']})."
            )
        )
