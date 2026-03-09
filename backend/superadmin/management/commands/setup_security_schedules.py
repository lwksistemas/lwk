"""
Management command para configurar schedules de segurança no Django-Q

Uso:
    python manage.py setup_security_schedules

Este comando cria/atualiza os schedules para:
1. Detecção de violações de segurança (a cada 5 minutos)
2. Limpeza de logs antigos (diariamente às 3h)
3. Envio de notificações (a cada 15 minutos)
4. Resumo diário de violações (diariamente às 8h)
5. WhatsApp: lembretes 24h e 2h antes
6. CRM Vendas: notificações de tarefas pendentes (a cada hora)
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'Configura schedules de segurança no Django-Q'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Configurando schedules de segurança...'))
        
        schedules_criados = 0
        schedules_atualizados = 0
        
        # 1. Detecção de violações de segurança (a cada 5 minutos)
        schedule, created = Schedule.objects.update_or_create(
            name='detect_security_violations',
            defaults={
                'func': 'superadmin.tasks.detect_security_violations',
                'schedule_type': Schedule.MINUTES,
                'minutes': 5,
                'repeats': -1,  # Repetir indefinidamente
            }
        )
        
        if created:
            schedules_criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Schedule criado: {schedule.name} (a cada 5 minutos)'
                )
            )
        else:
            schedules_atualizados += 1
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Schedule atualizado: {schedule.name} (a cada 5 minutos)'
                )
            )
        
        # 2. Limpeza de logs antigos (diariamente às 3h)
        schedule, created = Schedule.objects.update_or_create(
            name='cleanup_old_logs',
            defaults={
                'func': 'superadmin.tasks.cleanup_old_logs',
                'schedule_type': Schedule.DAILY,
                'repeats': -1,
                'next_run': None,  # Django-Q calculará automaticamente
            }
        )
        
        if created:
            schedules_criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Schedule criado: {schedule.name} (diariamente às 3h)'
                )
            )
        else:
            schedules_atualizados += 1
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Schedule atualizado: {schedule.name} (diariamente às 3h)'
                )
            )
        
        # 3. Envio de notificações (a cada 15 minutos)
        schedule, created = Schedule.objects.update_or_create(
            name='send_security_notifications',
            defaults={
                'func': 'superadmin.tasks.send_security_notifications',
                'schedule_type': Schedule.MINUTES,
                'minutes': 15,
                'repeats': -1,
            }
        )
        
        if created:
            schedules_criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Schedule criado: {schedule.name} (a cada 15 minutos)'
                )
            )
        else:
            schedules_atualizados += 1
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Schedule atualizado: {schedule.name} (a cada 15 minutos)'
                )
            )
        
        # 4. Resumo diário de violações (diariamente às 8h)
        schedule, created = Schedule.objects.update_or_create(
            name='send_daily_summary',
            defaults={
                'func': 'superadmin.tasks.send_daily_summary',
                'schedule_type': Schedule.DAILY,
                'repeats': -1,
                'next_run': None,  # Django-Q calculará automaticamente
            }
        )
        
        if created:
            schedules_criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Schedule criado: {schedule.name} (diariamente às 8h)'
                )
            )
        else:
            schedules_atualizados += 1
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Schedule atualizado: {schedule.name} (diariamente às 8h)'
                )
            )
        
        # 5. WhatsApp: lembretes 24h antes (diariamente às 8h)
        schedule, created = Schedule.objects.update_or_create(
            name='whatsapp_lembretes_24h',
            defaults={
                'func': 'whatsapp.tasks.send_lembretes_24h_whatsapp',
                'schedule_type': Schedule.DAILY,
                'repeats': -1,
            }
        )
        if created:
            schedules_criados += 1
        else:
            schedules_atualizados += 1
        self.stdout.write(
            self.style.SUCCESS(f'✅ Schedule: {schedule.name} (diário)')
        )
        
        # 6. WhatsApp: lembretes 2h antes (a cada 30 min)
        schedule, created = Schedule.objects.update_or_create(
            name='whatsapp_lembretes_2h',
            defaults={
                'func': 'whatsapp.tasks.send_lembretes_2h_whatsapp',
                'schedule_type': Schedule.MINUTES,
                'minutes': 30,
                'repeats': -1,
            }
        )
        if created:
            schedules_criados += 1
        else:
            schedules_atualizados += 1
        self.stdout.write(
            self.style.SUCCESS(f'✅ Schedule: {schedule.name} (a cada 30 min)')
        )

        # 7. CRM Vendas: notificações de tarefas pendentes (a cada hora)
        schedule, created = Schedule.objects.update_or_create(
            name='notificar_tarefas_crm',
            defaults={
                'func': 'crm_vendas.tasks.notificar_tarefas_crm',
                'schedule_type': Schedule.MINUTES,
                'minutes': 60,
                'repeats': -1,
            }
        )
        if created:
            schedules_criados += 1
        else:
            schedules_atualizados += 1
        self.stdout.write(
            self.style.SUCCESS(f'✅ Schedule: {schedule.name} (a cada hora)')
        )
        
        # Resumo
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Configuração concluída!'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   - Schedules criados: {schedules_criados}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'   - Schedules atualizados: {schedules_atualizados}'
            )
        )
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                '⚠️  IMPORTANTE: Para que os schedules funcionem, você precisa:'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '   1. Iniciar o cluster do Django-Q: python manage.py qcluster'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '   2. Manter o cluster rodando em background (use supervisor, systemd, etc.)'
            )
        )
        self.stdout.write('')
