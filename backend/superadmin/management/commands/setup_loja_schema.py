"""
Cria o schema da loja no PostgreSQL (se não existir) e aplica as migrations
para que as tabelas (ex.: clinica_beleza) existam no schema isolado.

IMPORTANTE: Sem rodar este comando, a loja NÃO terá tabelas no schema isolado
e nada será salvo (agendamentos, pacientes, etc.). Sempre rodar após criar uma nova loja.

Uso (produção Heroku):
  heroku run "cd backend && python manage.py setup_loja_schema SLUG_DA_LOJA" --app lwksistemas
  Ex.: heroku run "cd backend && python manage.py setup_loja_schema felix-representacoes-000172" --app lwksistemas

Se a loja CRM já existia antes do schema por loja e dá "relation crm_vendas_lead does not exist":
  heroku run "cd backend && python manage.py setup_loja_schema SLUG_DA_LOJA --force-crm" --app lwksistemas

Uso (local):
  python backend/manage.py setup_loja_schema SLUG_DA_LOJA
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings
from superadmin.models import Loja
import os


class Command(BaseCommand):
    help = 'Cria schema da loja (se não existir) e aplica migrations no schema isolado'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug da loja (ex: teste-5889)')
        parser.add_argument(
            '--force-crm',
            action='store_true',
            help='Remove estado de migração do crm_vendas no schema e reaplica (corrige "relation does not exist")',
        )

    def handle(self, *args, **options):
        slug = options['slug'].strip()

        self.stdout.write('\n' + '='*60)
        self.stdout.write('🔧 Setup schema e tabelas para loja')
        self.stdout.write('='*60 + '\n')

        loja = Loja.objects.filter(slug__iexact=slug).first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'❌ Loja com slug "{slug}" não encontrada'))
            return

        db_name = loja.database_name
        schema_name = db_name.replace('-', '_')

        self.stdout.write(f'Loja: {loja.nome} (ID: {loja.id})')
        self.stdout.write(f'Database name: {db_name}')
        self.stdout.write(f'Schema: {schema_name}\n')

        # 1. Criar schema se não existir
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = %s
            """, [schema_name])
            if cursor.fetchone():
                self.stdout.write(self.style.SUCCESS(f'✅ Schema "{schema_name}" já existe'))
            else:
                try:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                    self.stdout.write(self.style.SUCCESS(f'✅ Schema "{schema_name}" criado'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Erro ao criar schema: {e}'))
                    return

        # 2. Registrar banco nas configurações (para migrate)
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            self.stdout.write(self.style.ERROR('❌ DATABASE_URL não configurada'))
            return

        from core.db_config import ensure_loja_database_config
        if ensure_loja_database_config(db_name, conn_max_age=600):
            self.stdout.write(self.style.SUCCESS('✅ Banco configurado em settings.DATABASES'))

        # 3. (Opcional) Forçar reaplicação do CRM: remove estado de migração no schema
        force_crm = options.get('force_crm', False)
        if force_crm and db_name in settings.DATABASES:
            from django.db import connections
            try:
                with connections[db_name].cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM django_migrations WHERE app = %s",
                        ['crm_vendas'],
                    )
                    n = cursor.rowcount
                self.stdout.write(self.style.WARNING(f'  Estado crm_vendas removido ({n} registros). Reaplicando migrações.\n'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  force-crm: {e}\n'))

        # 4. Aplicar migrations no schema da loja
        tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
        base_apps = ['stores', 'products']
        tipo_apps = {
            'clinica-de-estetica': ['clinica_estetica'],
            'clinica-da-beleza': ['clinica_beleza'],
            'e-commerce': ['ecommerce'],
            'restaurante': ['restaurante'],
            'servicos': ['servicos'],
            'cabeleireiro': ['cabeleireiro'],
            'crm-vendas': ['crm_vendas'],
        }
        apps_to_migrate = base_apps + tipo_apps.get(tipo_slug, [])

        self.stdout.write(f'\nMigrando apps: {", ".join(apps_to_migrate)}\n')
        for app in apps_to_migrate:
            try:
                extra = {}
                if app == 'crm_vendas' and force_crm:
                    extra['fake_initial'] = True
                call_command('migrate', app, '--database', db_name, verbosity=1, **extra)
                self.stdout.write(self.style.SUCCESS(f'  ✅ {app}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠️ {app}: {e}'))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ Setup concluído. A loja pode passar a salvar dados no schema isolado.'))
        self.stdout.write('='*60 + '\n')
