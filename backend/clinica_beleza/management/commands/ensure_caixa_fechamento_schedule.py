"""Agenda o fechamento do caixa que passou das 23:59."""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Fecha automaticamente o caixa esquecido aberto depois das 23:59."

    def handle(self, *args, **options):
        schedule, created = Schedule.objects.update_or_create(
            name="clinica_caixa_fechamento_diario",
            defaults={
                "func": "clinica_beleza.venda_produto_service.fechar_caixas_esquecidos",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
        )
        acao = "criado" if created else "atualizado"
        self.stdout.write(self.style.SUCCESS(
            f"Schedule clinica_caixa_fechamento_diario {acao} (a cada 15 min)."
        ))
