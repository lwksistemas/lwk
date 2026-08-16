"""Management command para configurar schedules de segurança no Django-Q

Uso:
    python manage.py setup_security_schedules

Este comando cria/atualiza os schedules para:
1. Detecção de violações de segurança (a cada 5 minutos)
2. Limpeza de logs antigos (diariamente às 3h)
3. Envio de notificações (a cada 15 minutos)
4. Resumo diário de violações (diariamente às 8h)
5. WhatsApp: lembretes 24h e 2h antes; link de confirmação nos dias configurados
6. CRM Vendas: notificações de tarefas pendentes (a cada hora)
7. Backups automáticos por email (a cada 15 minutos, na madrugada por slot da loja)

Em Magalu rode via worker django-q ou scheduler local.
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Configura schedules de segurança no Django-Q"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Configurando schedules de segurança..."))

        schedules_criados = 0
        schedules_atualizados = 0

        def _upsert(name: str, defaults: dict, label: str) -> None:
            nonlocal schedules_criados, schedules_atualizados
            schedule, created = Schedule.objects.update_or_create(name=name, defaults=defaults)
            if created:
                schedules_criados += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Schedule criado: {schedule.name} ({label})"))
            else:
                schedules_atualizados += 1
                self.stdout.write(self.style.WARNING(f"⚠️  Schedule atualizado: {schedule.name} ({label})"))

        # 1. Detecção de violações de segurança (a cada 5 minutos)
        _upsert(
            "detect_security_violations",
            {
                "func": "superadmin.tasks.detect_security_violations",
                "schedule_type": Schedule.MINUTES,
                "minutes": 5,
                "repeats": -1,
            },
            "a cada 5 minutos",
        )

        # 2. Limpeza de logs antigos (diariamente às 3h)
        _upsert(
            "cleanup_old_logs",
            {
                "func": "superadmin.tasks.cleanup_old_logs",
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
                "next_run": None,
            },
            "diariamente",
        )

        # 3. Envio de notificações (a cada 15 minutos)
        _upsert(
            "send_security_notifications",
            {
                "func": "superadmin.tasks.send_security_notifications",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
            "a cada 15 minutos",
        )

        # 4. Resumo diário de violações (diariamente às 8h)
        _upsert(
            "send_daily_summary",
            {
                "func": "superadmin.tasks.send_daily_summary",
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
                "next_run": None,
            },
            "diariamente",
        )

        # 5. WhatsApp: lembretes 24h antes (diariamente às 8h)
        _upsert(
            "whatsapp_lembretes_24h",
            {
                "func": "whatsapp.tasks.send_lembretes_24h_whatsapp",
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
            },
            "diário",
        )

        # 6. WhatsApp: lembretes 2h antes (a cada 30 min)
        _upsert(
            "whatsapp_lembretes_2h",
            {
                "func": "whatsapp.tasks.send_lembretes_2h_whatsapp",
                "schedule_type": Schedule.MINUTES,
                "minutes": 30,
                "repeats": -1,
            },
            "a cada 30 min",
        )

        # 6b. WhatsApp: link de confirmação nos dias configurados (a cada 15 min)
        _upsert(
            "whatsapp_confirmacoes_agendadas",
            {
                "func": "whatsapp.tasks.send_confirmacoes_agendadas_whatsapp",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
            "a cada 15 min",
        )

        # 7. CRM Vendas: notificações de tarefas pendentes (a cada hora)
        _upsert(
            "notificar_tarefas_crm",
            {
                "func": "crm_vendas.tasks.notificar_tarefas_crm",
                "schedule_type": Schedule.MINUTES,
                "minutes": 60,
                "repeats": -1,
            },
            "a cada hora",
        )

        # 8. Backups automáticos por email
        # Roda a cada 15 min; a task só envia se estiver no slot 00:00–04:45 da loja.
        _upsert(
            "executar_backups_automaticos",
            {
                "func": "superadmin.tasks.executar_backups_automaticos",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
            "a cada 15 min (slots noturnos)",
        )

        # Resumo
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("✅ Configuração concluída!"))
        self.stdout.write(self.style.SUCCESS(f"   - Schedules criados: {schedules_criados}"))
        self.stdout.write(self.style.SUCCESS(f"   - Schedules atualizados: {schedules_atualizados}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "⚠️  IMPORTANTE: o worker django-q (qcluster) precisa estar rodando para os schedules.",
            ),
        )
        self.stdout.write("")
