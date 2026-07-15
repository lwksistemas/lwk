"""Libera loja beta para testes com vencimento em 1 ano (remove aviso de assinatura)."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Libera loja de teste (inadimplência + vencimento em 1 ano). Aceita slug ou atalho."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            default="vendasbeta",
            help="Slug ou atalho da loja (ex.: luminademo, lumina-demo, vendasbeta)",
        )

    def handle(self, *args, **options):
        from superadmin.loja_utils import resolve_loja_by_slug_or_atalho
        from superadmin.models import FinanceiroLoja

        slug = options["slug"]
        loja = resolve_loja_by_slug_or_atalho(slug, is_active=False)
        if not loja:
            self.stdout.write(self.style.ERROR(f"Loja {slug} nao encontrada"))
            return

        try:
            financeiro = loja.financeiro
        except FinanceiroLoja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Loja {slug} sem financeiro"))
            return

        hoje = date.today()
        proximo_ano = hoje + timedelta(days=365)

        loja.is_blocked = False
        loja.blocked_at = None
        loja.blocked_reason = ""
        loja.days_overdue = 0
        loja.save(update_fields=["is_blocked", "blocked_at", "blocked_reason", "days_overdue"])

        financeiro.data_proxima_cobranca = proximo_ano
        financeiro.status_pagamento = "ativo"
        financeiro.save(update_fields=["data_proxima_cobranca", "status_pagamento"])

        label = loja.atalho or loja.slug
        self.stdout.write(
            self.style.SUCCESS(
                f"Loja {label} (slug={loja.slug}) liberada. "
                f"Proximo vencimento: {proximo_ano.isoformat()}",
            ),
        )
