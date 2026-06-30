"""Aplica bloqueio por inadimplência de assinatura (5 dias após vencimento)."""
from django.core.management.base import BaseCommand

from superadmin.services.assinatura_bloqueio_service import (
    DAYS_TO_BLOCK,
    aplicar_bloqueio_inadimplencia_loja,
    dias_atraso_assinatura,
)


class Command(BaseCommand):
    help = f'Marca lojas em atraso e bloqueia após {DAYS_TO_BLOCK} dias do vencimento'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Não grava alterações')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN: nenhuma alteração será salva\n'))

        from superadmin.models import Loja

        bloqueadas = 0
        atrasadas = 0
        for loja in Loja.objects.filter(is_active=True).select_related('financeiro').iterator():
            dias = dias_atraso_assinatura(loja)
            if dias >= DAYS_TO_BLOCK:
                bloqueadas += 1
            elif dias > 0:
                atrasadas += 1
            aplicar_bloqueio_inadimplencia_loja(loja, persistir=not dry_run)

        self.stdout.write(self.style.SUCCESS(
            f'Verificação concluída: {atrasadas} em atraso (<{DAYS_TO_BLOCK}d), '
            f'{bloqueadas} para bloqueio (>={DAYS_TO_BLOCK}d)'
        ))
