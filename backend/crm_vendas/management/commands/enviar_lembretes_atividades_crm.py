"""Envia lembretes pendentes de atividades CRM (manual ou diagnóstico)."""
from django.core.management.base import BaseCommand

from crm_vendas.atividade_lembrete_tasks import (
    send_lembretes_atividade_crm_2h,
    send_lembretes_atividade_crm_24h,
)


class Command(BaseCommand):
    help = "Processa lembretes WhatsApp 24h e 2h das atividades CRM"

    def handle(self, *args, **options):
        n24 = send_lembretes_atividade_crm_24h()
        n2 = send_lembretes_atividade_crm_2h()
        self.stdout.write(self.style.SUCCESS(f"Lembretes CRM: 24h={n24} | 2h={n2}"))
