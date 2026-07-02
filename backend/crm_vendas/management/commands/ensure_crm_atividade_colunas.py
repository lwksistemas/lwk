"""
Garante colunas de crm_vendas_atividade (conta_id, lembretes WhatsApp) nos tenants CRM.

Uso:
    python manage.py ensure_crm_atividade_colunas
    python manage.py ensure_crm_atividade_colunas --slug felix
"""
from django.core.management.base import BaseCommand

from core.db_config import ensure_loja_database_config
from crm_vendas.schema_service import patch_crm_vendas_atividade_columns_if_missing
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Aplica patches SQL de crm_vendas_atividade (0056/0061) por loja CRM.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Processar apenas loja com este slug/atalho')

    def handle(self, *args, **options):
        slug_filter = (options.get('slug') or '').strip().lower()
        ok = skip = 0

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
            try:
                patch_crm_vendas_atividade_columns_if_missing(db_name)
                self.stdout.write(f'{loja.slug}: patches de atividade OK')
                ok += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'{loja.slug}: {exc}'))
                skip += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído: {ok} loja(s) OK, {skip} pulada(s).'))
