"""Garante registro FinanceiroLoja para lojas ativas que ainda não possuem."""
from django.core.management.base import BaseCommand

from superadmin.models import FinanceiroLoja, Loja
from superadmin.services import FinanceiroService


class Command(BaseCommand):
    help = "Cria FinanceiroLoja para lojas ativas sem financeiro (corrige assinatura 404)"

    def handle(self, *args, **options):
        criados = 0
        for loja in Loja.objects.filter(is_active=True).select_related("plano"):
            if FinanceiroLoja.objects.filter(loja=loja).exists():
                continue
            try:
                FinanceiroService.criar_financeiro_loja(loja, dia_vencimento=10)
                criados += 1
                self.stdout.write(self.style.SUCCESS(f"Financeiro criado: {loja.slug}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro em {loja.slug}: {e}"))
        self.stdout.write(self.style.SUCCESS(f"Concluído. Financeiros criados: {criados}"))
