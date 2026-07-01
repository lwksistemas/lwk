"""Sincroniza receitas de comissão a partir de oportunidades closed_won."""
from django.core.management.base import BaseCommand

from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria/atualiza receitas de comissão no financeiro CRM para vendas já ganhas'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Slug ou atalho da loja (opcional)')
        parser.add_argument('--loja-id', type=int, help='ID da loja (opcional)')
        parser.add_argument('--dry-run', action='store_true', help='Simula sem gravar')

    def handle(self, *args, **options):
        from crm_vendas.services_financeiro import sincronizar_comissoes_retroativas
        from superadmin.loja_utils import resolve_loja_by_slug_or_atalho

        slug = options.get('slug')
        loja_id = options.get('loja_id')
        dry_run = options.get('dry_run', False)

        lojas = []
        if loja_id:
            lojas = list(Loja.objects.filter(id=loja_id, is_active=True))
        elif slug:
            loja = resolve_loja_by_slug_or_atalho(slug, is_active=True)
            lojas = [loja] if loja else []
        else:
            lojas = list(Loja.objects.filter(is_active=True).only('id', 'nome', 'slug', 'atalho'))

        if not lojas:
            self.stdout.write(self.style.ERROR('Nenhuma loja encontrada.'))
            return

        for loja in lojas:
            from core.db_config import ensure_loja_database_config
            from tenants.middleware import set_current_loja_id, set_current_tenant_db

            if not loja.database_name or not ensure_loja_database_config(loja.database_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f'SKIP {loja.slug}: banco indisponível'))
                continue
            set_current_loja_id(loja.id)
            set_current_tenant_db(loja.database_name)
            result = sincronizar_comissoes_retroativas(loja.id, dry_run=dry_run)
            label = loja.atalho or loja.slug
            self.stdout.write(
                self.style.SUCCESS(
                    f'{label}: analisadas={result["oportunidades_analisadas"]} '
                    f'criadas={result["criadas"]} atualizadas={result["atualizadas"]} '
                    f'ignoradas={result["ignoradas"]} dry_run={dry_run}'
                )
            )
