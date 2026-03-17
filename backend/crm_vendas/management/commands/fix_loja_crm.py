"""
Corrige schema e colunas do CRM para uma loja que está retornando erro 500.
Útil quando lojas novas ou migradas apresentam "Erro ao carregar dashboard" ou 500.

Uso (Heroku):
  heroku run "cd backend && python manage.py fix_loja_crm 41449198000172" --app lwksistemas

Uso (local):
  python manage.py fix_loja_crm SLUG_DA_LOJA
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection, connections
from django.conf import settings
from superadmin.models import Loja
import dj_database_url
import os


class Command(BaseCommand):
    help = 'Corrige schema e colunas CRM para loja com erro 500 (nova loja ou migrada)'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug da loja (ex: 41449198000172 ou minha-loja-000172)')
        parser.add_argument(
            '--force-crm',
            action='store_true',
            help='Força reaplicação das migrations do crm_vendas',
        )

    def handle(self, *args, **options):
        slug = options['slug'].strip()

        self.stdout.write('\n' + '='*60)
        self.stdout.write('🔧 Corrigindo CRM para loja')
        self.stdout.write('='*60 + '\n')

        loja = Loja.objects.filter(slug__iexact=slug).select_related('tipo_loja').first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'❌ Loja com slug "{slug}" não encontrada'))
            self.stdout.write('   Verifique se o slug está correto. O slug aparece na URL: /loja/SLUG/crm-vendas')
            return

        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
        if tipo_slug != 'crm-vendas':
            self.stdout.write(self.style.WARNING(f'⚠️ Loja "{loja.nome}" não é do tipo CRM Vendas (tipo: {tipo_slug})'))
            self.stdout.write('   Este comando é para lojas CRM. Continuando mesmo assim...\n')

        db_name = loja.database_name
        schema_name = db_name.replace('-', '_')

        self.stdout.write(f'Loja: {loja.nome} (ID: {loja.id}, slug: {loja.slug})')
        self.stdout.write(f'Schema: {schema_name}\n')

        # 1. Garantir que o banco está em settings.DATABASES
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            self.stdout.write(self.style.ERROR('❌ DATABASE_URL não configurada'))
            return

        if db_name not in settings.DATABASES:
            default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
            settings.DATABASES[db_name] = {
                **default_db,
                'OPTIONS': {'options': f'-c search_path={schema_name},public'},
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
                'CONN_MAX_AGE': 0,
                'CONN_HEALTH_CHECKS': False,
                'TIME_ZONE': None,
            }
            self.stdout.write(self.style.SUCCESS('✅ Banco configurado'))

        # 2. Criar schema se não existir (usa default connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name]
            )
            if cursor.fetchone():
                self.stdout.write(self.style.SUCCESS(f'✅ Schema "{schema_name}" existe'))
            else:
                try:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                    self.stdout.write(self.style.SUCCESS(f'✅ Schema "{schema_name}" criado'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Erro ao criar schema: {e}'))
                    return

        # 3. Aplicar migrations (setup_loja_schema)
        self.stdout.write('\nAplicando migrations...')
        force_crm = options.get('force_crm', False)
        if force_crm and db_name in settings.DATABASES:
            try:
                with connections[db_name].cursor() as cur:
                    cur.execute("DELETE FROM django_migrations WHERE app = %s", ['crm_vendas'])
                    self.stdout.write(self.style.WARNING('  Estado crm_vendas resetado'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  force-crm: {e}'))

        base_apps = ['stores', 'products']
        tipo_apps = {
            'crm-vendas': ['crm_vendas'],
            'clinica-da-beleza': ['clinica_beleza', 'whatsapp'],
            'clinica-de-estetica': ['clinica_estetica'],
            'e-commerce': ['ecommerce'],
            'restaurante': ['restaurante'],
            'servicos': ['servicos'],
            'cabeleireiro': ['cabeleireiro'],
        }
        apps = base_apps + tipo_apps.get(tipo_slug, ['crm_vendas'])

        for app in apps:
            try:
                extra = {'fake_initial': True} if (app == 'crm_vendas' and force_crm) else {}
                call_command('migrate', app, '--database', db_name, verbosity=1, **extra)
                self.stdout.write(self.style.SUCCESS(f'  ✅ {app}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️ {app}: {e}'))

        # 4. Adicionar cpf_cnpj em crm_vendas_lead se faltando
        self.stdout.write('\nVerificando coluna cpf_cnpj em leads...')
        try:
            conn = connections[db_name]
            conn.ensure_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'crm_vendas_lead'
                """, [schema_name])
                if not cursor.fetchone():
                    self.stdout.write(self.style.WARNING('  Tabela crm_vendas_lead não existe (migrations podem ter falhado)'))
                else:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = 'crm_vendas_lead' AND column_name = 'cpf_cnpj'
                    """, [schema_name])
                    if cursor.fetchone():
                        self.stdout.write(self.style.SUCCESS('  ✅ cpf_cnpj já existe'))
                    else:
                        cursor.execute(
                            f'ALTER TABLE "{schema_name}"."crm_vendas_lead" ADD COLUMN IF NOT EXISTS cpf_cnpj VARCHAR(18) DEFAULT \'\''
                        )
                        self.stdout.write(self.style.SUCCESS('  ✅ Coluna cpf_cnpj adicionada'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  cpf_cnpj: {e}'))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ Concluído. Teste acessar a loja novamente.'))
        self.stdout.write('='*60 + '\n')
