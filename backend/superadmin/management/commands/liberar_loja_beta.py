"""Libera loja beta (vendasbeta) para testes com vencimento em 1 ano."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Libera a loja beta (vendasbeta) de inadimplencia e define vencimento em 1 ano'

    def add_arguments(self, parser):
        parser.add_argument('--slug', default='vendasbeta', help='Slug da loja a liberar')

    def handle(self, *args, **options):
        from superadmin.models import FinanceiroLoja, Loja

        slug = options['slug']
        loja = Loja.objects.filter(slug=slug).first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'Loja {slug} nao encontrada'))
            return

        try:
            financeiro = loja.financeiro
        except FinanceiroLoja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Loja {slug} sem financeiro'))
            return

        hoje = date.today()
        proximo_ano = hoje + timedelta(days=365)

        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ''
        loja.days_overdue = 0
        loja.save(update_fields=['is_blocked', 'blocked_at', 'blocked_reason', 'days_overdue'])

        financeiro.data_proxima_cobranca = proximo_ano
        financeiro.status_pagamento = 'ativo'
        financeiro.save(update_fields=['data_proxima_cobranca', 'status_pagamento'])

        self.stdout.write(self.style.SUCCESS(
            f'Loja {slug} liberada. Proximo vencimento: {proximo_ano.isoformat()}'
        ))
