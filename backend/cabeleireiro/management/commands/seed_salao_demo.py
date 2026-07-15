"""Seed mínimo para loja tipo cabeleireiro (demo / beta).

Uso:
  python manage.py seed_salao_demo --slug meusalao
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = "Cria dados demo (profissional, serviços, agendamentos de hoje) no salão."

    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str, required=True)

    def handle(self, *args, **options):
        slug = (options.get("slug") or "").strip().lower()
        loja = Loja.objects.filter(slug__iexact=slug).select_related("tipo_loja").first()
        if not loja:
            self.stderr.write(self.style.ERROR(f"Loja slug={slug} não encontrada"))
            return
        tipo = (loja.tipo_loja.slug if loja.tipo_loja else "") or ""
        if tipo != "cabeleireiro":
            self.stderr.write(self.style.WARNING(f"Loja {slug} tipo={tipo} (esperado cabeleireiro) — seguindo mesmo assim"))

        db = loja.database_name
        if not ensure_loja_database_config(db, conn_max_age=0):
            self.stderr.write(self.style.ERROR("Falha ao configurar DB da loja"))
            return
        set_current_tenant_db(db)
        set_current_loja_id(loja.id)

        from cabeleireiro.models import Agendamento, Cliente, Profissional, Servico

        prof, _ = Profissional.objects.get_or_create(
            loja_id=loja.id,
            nome="Beatriz Lima",
            defaults={"telefone": "11999990000", "especialidade": "Colorista", "email": "beatriz@salao.demo"},
        )
        s1, _ = Servico.objects.get_or_create(
            loja_id=loja.id,
            nome="Corte feminino",
            defaults={"duracao_minutos": 45, "preco": Decimal("80.00"), "categoria": "Corte"},
        )
        s2, _ = Servico.objects.get_or_create(
            loja_id=loja.id,
            nome="Escova",
            defaults={"duracao_minutos": 40, "preco": Decimal("60.00"), "categoria": "Finalização"},
        )
        c1, _ = Cliente.objects.get_or_create(
            loja_id=loja.id,
            nome="Mariana Alves",
            defaults={"telefone": "11988887777", "email": "mariana@email.com"},
        )
        c2, _ = Cliente.objects.get_or_create(
            loja_id=loja.id,
            nome="Ana Costa",
            defaults={"telefone": "11977776666"},
        )
        c3, _ = Cliente.objects.get_or_create(
            loja_id=loja.id,
            nome="Carla Souza",
            defaults={"telefone": "11966665555"},
        )

        hoje = timezone.localdate()
        base_hora = datetime.strptime("09:00", "%H:%M").time()
        slots = [
            (c1, s1, base_hora),
            (c2, s2, (datetime.combine(hoje, base_hora) + timedelta(hours=1)).time()),
            (c3, s1, (datetime.combine(hoje, base_hora) + timedelta(hours=2)).time()),
        ]
        criados = 0
        for cliente, servico, hora in slots:
            _, created = Agendamento.objects.get_or_create(
                loja_id=loja.id,
                cliente=cliente,
                data=hoje,
                hora_inicio=hora,
                defaults={
                    "profissional": prof,
                    "servico": servico,
                    "valor": servico.preco,
                    "status": Agendamento.STATUS_SCHEDULED,
                },
            )
            if created:
                criados += 1

        self.stdout.write(self.style.SUCCESS(
            f"OK loja={slug}: profissional={prof.id}, serviços=2, clientes=3, agendamentos novos={criados}",
        ))
