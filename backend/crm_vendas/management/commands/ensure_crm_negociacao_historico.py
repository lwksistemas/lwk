"""
Garante colunas e tabela do histórico de negociação CRM (0069) nos tenants.

Uso:
    python manage.py ensure_crm_negociacao_historico
    python manage.py ensure_crm_negociacao_historico --slug felix
"""
from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from crm_vendas.negociacao_historico_schema_ensure import ensure_negociacao_historico_schema
from crm_vendas.schema_service import patch_crm_migration_0067_if_orphan
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Aplica patches SQL do histórico de negociação CRM (0069) por loja.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        ok = patched = skip = 0

        for loja in Loja.objects.filter(is_active=True, database_created=True, tipo_loja__slug='crm-vendas'):
            if slug_filter and slug_filter not in (
                (loja.slug or '').lower(),
                (getattr(loja, 'atalho', None) or '').lower(),
            ):
                continue
            db_name = loja.database_name
            if not ensure_loja_database_config(db_name, conn_max_age=0):
                self.stdout.write(self.style.WARNING(f'Pulando {loja.slug}: DB indisponível'))
                skip += 1
                continue
            schema_name = db_name.replace('-', '_')
            try:
                patch_crm_migration_0067_if_orphan(db_name)
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    applied = ensure_negociacao_historico_schema(cursor, schema_name)
                if applied:
                    self.stdout.write(self.style.SUCCESS(f'{loja.slug}: schema 0069 aplicado'))
                    patched += 1
                else:
                    self.stdout.write(f'{loja.slug}: já OK')
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{loja.slug}: {exc}'))
                skip += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Concluído: {ok} loja(s) verificada(s), {patched} corrigida(s), {skip} falha(s).',
            ),
        )
