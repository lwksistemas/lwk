"""Agenda o job Django-Q que finaliza consultas esquecidas."""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Agenda auto-finalização de consultas 5h após o fim do agendamento"

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.update_or_create(
            name="clinica_auto_finalizar_consultas",
            defaults={
                "func": "clinica_beleza.consulta_auto_finalizar_service.finalizar_consultas_esquecidas",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
        )
        acao = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(
            f"Schedule clinica_auto_finalizar_consultas {acao} (a cada 15 min)."
        ))
