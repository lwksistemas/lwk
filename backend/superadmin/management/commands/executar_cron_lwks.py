"""
Cron central LWK (serviço Railway lwks-cron).

Executa a cada 15 minutos:
- Lembretes WhatsApp de atividades CRM (24h e 2h antes)
- Lembretes WhatsApp de agendamentos clínica (2h; 24h entre 7h–9h)
- Marca Faltou (NO_SHOW) 2h após horário sem chegada
- Backups automáticos por email (no minuto :00)

Deploy:
  railway up --service lwks-cron -c railway.cron.toml
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Cron LWK: lembretes WhatsApp (CRM + clínica) e backups automáticos'

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        self.stdout.write(self.style.SUCCESS(f'=== Cron LWK {now.isoformat()} ==='))

        from crm_vendas.atividade_lembrete_tasks import (
            send_lembretes_atividade_crm_24h,
            send_lembretes_atividade_crm_2h,
        )
        from whatsapp.tasks import send_lembretes_2h_whatsapp
        from clinica_beleza.agenda_no_show_service import marcar_faltas_agenda_automatico

        crm_24h = send_lembretes_atividade_crm_24h()
        crm_2h = send_lembretes_atividade_crm_2h()
        clin_2h = send_lembretes_2h_whatsapp()
        no_show = marcar_faltas_agenda_automatico()
        self.stdout.write(f'  CRM atividades: 24h={crm_24h} | 2h={crm_2h}')
        self.stdout.write(f'  Clínica 2h: {clin_2h} | NO_SHOW auto: {no_show}')

        if 7 <= now.hour <= 9:
            from whatsapp.tasks import send_lembretes_24h_whatsapp
            clin_24h = send_lembretes_24h_whatsapp()
            self.stdout.write(f'  Clínica 24h: {clin_24h}')
            call_command('notificar_tarefas_crm', verbosity=1)

        if now.minute == 0:
            call_command('executar_backups_automaticos', verbosity=1)

        self.stdout.write(self.style.SUCCESS('=== Cron LWK concluído ==='))
