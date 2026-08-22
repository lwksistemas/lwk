"""Garante TipoLoja Clínica Geral + plano (idempotente)."""
from decimal import Decimal

from django.core.management.base import BaseCommand

from superadmin.models import PlanoAssinatura, TipoLoja


class Command(BaseCommand):
    help = "Cria/atualiza o tipo de app Clínica Geral e o plano básico."

    def handle(self, *args, **options):
        tipo, created = TipoLoja.objects.update_or_create(
            slug="clinica-geral",
            defaults={
                "nome": "Clínica Geral",
                "codigo": "CLIGER",
                "descricao": "Consultório médico: agenda, pacientes e consultas. Sem estética.",
                "dashboard_template": "clinica-geral",
                "cor_primaria": "#2F2E5B",
                "cor_secundaria": "#0D9B9B",
                "tem_produtos": False,
                "tem_servicos": True,
                "tem_agendamento": True,
                "tem_delivery": False,
                "tem_estoque": False,
                "is_active": True,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(f"{'Criado' if created else 'Atualizado'} tipo: {tipo.nome} (id={tipo.id})")
        )

        plano, p_created = PlanoAssinatura.objects.update_or_create(
            slug="basico-clinica-geral",
            defaults={
                "nome": "Básico Clínica Geral",
                "descricao": "Agenda, pacientes e consultas do consultório.",
                "preco_mensal": Decimal("139.00"),
                "preco_anual": Decimal("1390.00"),
                "max_usuarios": 5,
                "max_pedidos_mes": 2000,
                "espaco_storage_gb": 5,
                "tem_relatorios_avancados": False,
                "tem_suporte_prioritario": False,
                "is_active": True,
            },
        )
        plano.tipos_loja.add(tipo)
        self.stdout.write(
            f"  {'Criado' if p_created else 'Atualizado'} plano: {plano.nome}"
        )
        self.stdout.write(self.style.SUCCESS("Clínica Geral pronta em tipos-app / planos."))
