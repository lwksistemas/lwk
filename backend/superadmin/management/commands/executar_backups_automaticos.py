"""Comando para executar a verificação de backups automáticos agendados.

Chama executar_backups_automaticos(): para cada loja com backup automático ativo,
verifica se está no horário e se ainda não rodou hoje; se sim, processa o backup
e envia por email para o owner da loja.

Em Magalu o agendamento é via Django-Q (worker):
  python manage.py setup_security_schedules
  → schedule "executar_backups_automaticos" a cada 15 min

Slots noturnos: 00:00–04:45 (horário de Brasília), um por loja.
"""
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Verifica backups automáticos agendados e processa os que estão no horário. "
        "No Magalu rode via Django-Q (setup_security_schedules)."
    )

    def handle(self, *args, **options):
        from superadmin.tasks import executar_backups_automaticos

        self.stdout.write(
            self.style.SUCCESS(f"=== Verificação de backups automáticos em {timezone.localtime(timezone.now())} ==="),
        )

        result = executar_backups_automaticos()

        self.stdout.write(
            self.style.SUCCESS(
                f"Verificação concluída: {result['total_agendados']} backup(s) agendado(s) "
                f"(configurações verificadas: {result['total_verificados']}).",
            ),
        )
