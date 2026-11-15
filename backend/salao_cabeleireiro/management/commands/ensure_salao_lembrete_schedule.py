"""Agenda o lembrete do salão. A tarefa não envia nada enquanto a loja deixar a regra desligada."""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Agenda o lembrete de WhatsApp do salão a cada 15 minutos."

    def handle(self, *args, **options):
        _agenda, criada = Schedule.objects.update_or_create(
            name="salao_lembrete_whatsapp",
            defaults={
                "func": "salao_cabeleireiro.lembretes.enviar_lembretes_salao",
                "schedule_type": Schedule.MINUTES,
                "minutes": 15,
                "repeats": -1,
            },
        )
        acao = "criado" if criada else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Schedule salao_lembrete_whatsapp {acao}."))
