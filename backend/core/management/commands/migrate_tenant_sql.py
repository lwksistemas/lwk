"""
Aplica SQL customizado em schemas de lojas, filtrando por tipo de loja ou app Django.

Usa o mapeamento TIPO_LOJA_EXTRA_APPS para saber quais tipos de loja possuem
quais apps — evita rodar SQL em schemas que não têm as tabelas.

Uso:
    # Rodar SQL apenas em lojas que têm o app crm_vendas:
    python manage.py migrate_tenant_sql --app crm_vendas --sql "ALTER TABLE ..."

    # Rodar SQL em lojas de um tipo específico:
    python manage.py migrate_tenant_sql --tipo-loja crm-vendas --sql "ALTER TABLE ..."

    # Verificar se tabela existe antes de rodar:
    python manage.py migrate_tenant_sql --app crm_vendas --check-table crm_vendas_conta --sql "ALTER TABLE ..."

    # Rodar em uma loja específica:
    python manage.py migrate_tenant_sql --loja-id 5 --sql "SELECT 1"

    # Listar lojas e seus tipos:
    python manage.py migrate_tenant_sql --list

    # Dry-run (mostra o que faria sem executar):
    python manage.py migrate_tenant_sql --app crm_vendas --sql "ALTER TABLE ..." --dry-run

    # Executar arquivo SQL:
    python manage.py migrate_tenant_sql --app crm_vendas --sql-file scripts/meu_sql.sql
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja
from superadmin.services.database_schema_service import TIPO_LOJA_EXTRA_APPS


def _tipos_loja_para_app(app_label: str) -> list[str]:
    """Retorna slugs de tipo_loja que incluem o app_label dado."""
    # stores e products existem em TODOS os tipos
    if app_label in ('stores', 'products'):
        return []  # vazio = todos
    resultado = []
    for tipo_slug, apps in TIPO_LOJA_EXTRA_APPS.items():
        if app_label in apps:
            resultado.append(tipo_slug)
    return resultado


class Command(BaseCommand):
    help = 'Aplica SQL em schemas de lojas filtrado por tipo de loja ou app Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='App Django (ex: crm_vendas). Filtra automaticamente pelos tipos de loja que possuem esse app.',
        )
        parser.add_argument(
            '--tipo-loja',
            type=str,
            help='Slug do tipo de loja (ex: crm-vendas, hotel). Aceita múltiplos separados por vírgula.',
        )
        parser.add_argument(
            '--loja-id',
            type=int,
            help='ID específico de uma loja.',
        )
        parser.add_argument(
            '--sql',
            type=str,
            help='SQL inline para executar em cada schema.',
        )
        parser.add_argument(
            '--sql-file',
            type=str,
            help='Caminho para arquivo .sql para executar.',
        )
        parser.add_argument(
            '--check-table',
            type=str,
            help='Só executa se esta tabela existir no schema (ex: crm_vendas_conta).',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Apenas lista as lojas filtradas.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria executado sem rodar.',
        )

    def handle(self, *args, **options):
        app_label = options.get('app')
        tipo_loja_slug = options.get('tipo_loja')
        loja_id = options.get('loja_id')
        sql_inline = options.get('sql')
        sql_file = options.get('sql_file')
        check_table = options.get('check_table')
        list_only = options.get('list')
        dry_run = options.get('dry_run')

        # Resolver tipos de loja a partir do app
        slugs_filtro = []
        if app_label:
            slugs_filtro = _tipos_loja_para_app(app_label)
            if slugs_filtro:
                self.stdout.write(f'📦 App "{app_label}" pertence aos tipos: {", ".join(slugs_filtro)}')
            else:
                self.stdout.write(f'📦 App "{app_label}" existe em todos os tipos de loja')

        if tipo_loja_slug:
            slugs_filtro = [s.strip() for s in tipo_loja_slug.split(',')]

        # Buscar lojas
        qs = Loja.objects.filter(is_active=True, database_created=True).select_related('tipo_loja')
        if loja_id:
            qs = qs.filter(id=loja_id)
        if slugs_filtro:
            qs = qs.filter(tipo_loja__slug__in=slugs_filtro)

        lojas = list(qs.order_by('id'))

        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja encontrada com os filtros informados.'))
            return

        self.stdout.write(f'\n📋 {len(lojas)} loja(s) encontrada(s)\n')

        if list_only:
            for loja in lojas:
                tipo_nome = loja.tipo_loja.nome if loja.tipo_loja else '?'
                tipo_slug = loja.tipo_loja.slug if loja.tipo_loja else '?'
                self.stdout.write(
                    f'  ID={loja.id} | {loja.nome} | tipo={tipo_nome} ({tipo_slug}) | schema={loja.database_name}'
                )
            self.stdout.write('')
            # Mostrar mapeamento de referência
            self.stdout.write('📖 Mapeamento TIPO_LOJA_EXTRA_APPS:')
            for slug, apps in sorted(TIPO_LOJA_EXTRA_APPS.items()):
                self.stdout.write(f'  {slug}: {", ".join(apps)}')
            return

        # Validar SQL
        sql_to_run = None
        if sql_inline:
            sql_to_run = sql_inline
        elif sql_file:
            import os
            if not os.path.exists(sql_file):
                self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {sql_file}'))
                return
            with open(sql_file, 'r') as f:
                sql_to_run = f.read()

        if not sql_to_run:
            self.stdout.write(self.style.ERROR('Informe --sql ou --sql-file.'))
            return

        sucesso = 0
        erros = 0
        pulados = 0

        for loja in lojas:
            schema = loja.database_name
            tipo_nome = loja.tipo_loja.nome if loja.tipo_loja else '?'
            self.stdout.write(f'\n🔄 {loja.nome} (schema={schema}, tipo={tipo_nome})')

            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SET search_path TO {schema}')

                    if check_table:
                        cursor.execute(
                            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                            "WHERE table_schema = %s AND table_name = %s)",
                            [schema, check_table],
                        )
                        if not cursor.fetchone()[0]:
                            self.stdout.write(self.style.WARNING(
                                f'  ⏭️  Tabela {check_table} não existe — pulando'
                            ))
                            pulados += 1
                            continue

                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(
                            f'  🔍 [DRY-RUN] Executaria SQL ({len(sql_to_run)} chars)'
                        ))
                        sucesso += 1
                        continue

                    cursor.execute(sql_to_run)
                    connection.commit()
                    self.stdout.write(self.style.SUCCESS('  ✅ OK'))
                    sucesso += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {e}'))
                erros += 1
                try:
                    connection.rollback()
                except Exception:
                    pass

        try:
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')
        except Exception:
            pass

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'✅ Sucesso: {sucesso} | ❌ Erros: {erros} | ⏭️  Pulados: {pulados}')
        self.stdout.write(f'{"="*60}\n')
