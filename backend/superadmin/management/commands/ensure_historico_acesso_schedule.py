"""Agenda a limpeza do histórico no django-q, domingo às 3h."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule


def proximo_domingo_as_3h():
    agora = timezone.localtime()
    dias = (6 - agora.weekday()) % 7
    alvo = (agora + timedelta(days=dias)).replace(hour=3, minute=0, second=0, microsecond=0)
    if alvo <= agora:
        alvo += timedelta(days=7)
    return alvo


class Command(BaseCommand):
    help = "Agenda limpar_historico_acesso para domingo às 3h"

    def handle(self, *args, **options):
        agenda, created = Schedule.objects.get_or_create(
            name="limpar_historico_acesso",
            defaults={
                "func": "superadmin.historico_limpeza.limpar_historico_acesso",
                "schedule_type": Schedule.WEEKLY,
                "repeats": -1,
                "next_run": proximo_domingo_as_3h(),
            },
        )
        if not created:
            agenda.func = "superadmin.historico_limpeza.limpar_historico_acesso"
            agenda.schedule_type = Schedule.WEEKLY
            agenda.repeats = -1
            if agenda.next_run is None:
                agenda.next_run = proximo_domingo_as_3h()
            agenda.save(update_fields=["func", "schedule_type", "repeats", "next_run"])
        acao = "criada" if created else "atualizada"
        self.stdout.write(self.style.SUCCESS(
            f"Agenda limpar_historico_acesso {acao} para {timezone.localtime(agenda.next_run):%d/%m/%Y %H:%M}."
        ))
