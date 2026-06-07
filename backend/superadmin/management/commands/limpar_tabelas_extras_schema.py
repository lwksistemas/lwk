"""
Remove tabelas legado/não esperadas do schema de uma loja (por tipo de app).

Uso:
    python manage.py limpar_tabelas_extras_schema --slug harmonis --dry-run
    python manage.py limpar_tabelas_extras_schema --slug harmonis
"""
from django.core.management.base import BaseCommand
from django.db import connections

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from superadmin.services.database_schema_service import get_apps_esperados_para_loja
from superadmin.services.schema_audit_service import listar_tabelas_extras_no_schema


class Command(BaseCommand):
    help = 'Remove tabelas não esperadas para o tipo da loja no schema PostgreSQL.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, required=True, help='Slug ou atalho da loja')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas lista tabelas que seriam removidas',
        )

    def handle(self, *args, **options):
        slug = (options.get('slug') or '').strip().lower()
        dry_run = options.get('dry_run', False)

        loja = (
            Loja.objects.filter(slug__iexact=slug).first()
            or Loja.objects.filter(atalho__iexact=slug).first()
        )
        if not loja:
            self.stdout.write(self.style.ERROR(f'Loja não encontrada: {slug}'))
            return

        if not loja.database_name or not loja.database_created:
            self.stdout.write(self.style.ERROR('Loja sem schema configurado.'))
            return

        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            self.stdout.write(self.style.ERROR('Não foi possível conectar ao schema da loja.'))
            return

        schema = loja.database_name.replace('-', '_')
        apps_esperados = get_apps_esperados_para_loja(loja)
        conn = connections[loja.database_name]

        extras = listar_tabelas_extras_no_schema(conn, schema, apps_esperados)
        if not extras:
            self.stdout.write(self.style.SUCCESS(f'{loja.nome}: nenhuma tabela extra.'))
            return

        self.stdout.write(
            f'{loja.nome} ({schema}): {len(extras)} tabela(s) extra(s) para {loja.tipo_loja.slug}'
        )
        for name in extras:
            self.stdout.write(f'  - {name}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: nada removido.'))
            return

        apps_removidos: set[str] = set()
        for table in extras:
            if table.startswith('cabeleireiro_'):
                apps_removidos.add('cabeleireiro')
            elif table.startswith('asaas_'):
                apps_removidos.add('asaas_integration')
            elif table.startswith('clinica_beleza_'):
                apps_removidos.add('clinica_beleza')
            elif table.startswith('clinica_'):
                apps_removidos.add('clinica_estetica')
            elif table.startswith('crm_vendas_'):
                apps_removidos.add('crm_vendas')
            elif table == 'django_admin_log':
                apps_removidos.add('admin')

        with conn.cursor() as cur:
            cur.execute('SET search_path TO %s, public', [schema])
            for table in extras:
                cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')

            for app in sorted(apps_removidos):
                cur.execute('DELETE FROM django_migrations WHERE app = %s', [app])
                self.stdout.write(f'  migrations removidas: {app}')

        self.stdout.write(self.style.SUCCESS(f'Concluído: {len(extras)} tabela(s) removida(s).'))
