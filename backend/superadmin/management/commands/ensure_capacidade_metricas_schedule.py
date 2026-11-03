"""Agenda a gravação do histórico de capacidade das VMs Magalu."""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Agenda registrar_metricas_capacidade a cada 15 minutos."

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.update_or_create(
            name="capacidade_metricas_servidores",
            defaults={
                "func": "superadmin.capacidade_metrics.registrar_metricas_periodicas",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
        )
        acao = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(
            f"Schedule capacidade_metricas_servidores {acao} (a cada 15 min)."
        ))
