"""Agenda a consulta das NF-e de fornecedor na SEFAZ."""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Agenda a busca de NF-e de fornecedor a cada hora."

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.update_or_create(
            name="clinica_nfe_entrada_fornecedor",
            defaults={
                "func": "clinica_beleza.estoque_nfe_pendente_service.sincronizar_nfe_fornecedores",
                "schedule_type": Schedule.MINUTES,
                "minutes": 60,
                "repeats": -1,
            },
        )
        acao = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(
            f"Schedule clinica_nfe_entrada_fornecedor {acao} (a cada 60 min)."
        ))
