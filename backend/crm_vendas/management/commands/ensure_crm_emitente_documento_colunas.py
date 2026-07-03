"""
Garante colunas emitente_* (migration 0068) em proposta/contrato nos tenants CRM.

Uso:
    python manage.py ensure_crm_emitente_documento_colunas
    python manage.py ensure_crm_emitente_documento_colunas --slug felix
"""
from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from crm_vendas.emitente_documento_schema_ensure import (
    emitente_columns_missing,
    ensure_emitente_documento_columns,
)
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona colunas emitente_* em proposta/contrato quando migration 0068 não aplicou no tenant.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        ok = fixed = skip = 0

        lojas = Loja.objects.filter(is_active=True, database_created=True).select_related('tipo_loja')
        for loja in lojas:
            tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
            if tipo_slug != 'crm-vendas':
                continue
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
                conn = connections[db_name]
                with conn.cursor() as cursor:
                    cursor.execute(f'SET search_path TO "{schema_name}", public')
                    if not emitente_columns_missing(cursor):
                        self.stdout.write(f'{loja.slug}: colunas emitente OK')
                        ok += 1
                        continue
                    if ensure_emitente_documento_columns(cursor, schema_name):
                        fixed += 1
                        self.stdout.write(self.style.SUCCESS(f'{loja.slug}: colunas emitente criadas'))
                    else:
                        skip += 1
                        self.stdout.write(self.style.ERROR(f'{loja.slug}: falha ao criar colunas'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{loja.slug}: {exc}'))
                skip += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Concluído: {ok} OK, {fixed} corrigida(s), {skip} pulada(s)/falha(s).'
            )
        )
