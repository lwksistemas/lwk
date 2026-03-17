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

        # 1-3. Usar schema_service para criar schema e aplicar migrations
        from crm_vendas.schema_service import configurar_schema_crm_loja
        if not configurar_schema_crm_loja(loja):
            self.stdout.write(self.style.ERROR('❌ Falha ao configurar schema'))
            return

        self.stdout.write(self.style.SUCCESS('✅ Schema e migrations configurados'))

        # 4. Force-crm: reaplicar migrations crm_vendas se solicitado
        force_crm = options.get('force_crm', False)
        if force_crm and db_name in settings.DATABASES:
            self.stdout.write('\nForce-crm: reaplicando migrations...')
            try:
                with connections[db_name].cursor() as cur:
                    cur.execute("DELETE FROM django_migrations WHERE app = %s", ['crm_vendas'])
                call_command('migrate', 'crm_vendas', '--database', db_name, verbosity=1, fake_initial=True)
                self.stdout.write(self.style.SUCCESS('  ✅ crm_vendas reaplicado'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  force-crm: {e}'))

        # 5. Adicionar cpf_cnpj em crm_vendas_lead se faltando (fallback para schemas antigos)
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

        # 5. Adicionar proposta_conteudo_padrao em crm_vendas_config se faltando
        if tipo_slug == 'crm-vendas':
            self.stdout.write('\nVerificando coluna proposta_conteudo_padrao em crm_vendas_config...')
            try:
                with connections[db_name].cursor() as cursor:
                    cursor.execute("""
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = 'crm_vendas_config'
                    """, [schema_name])
                    if cursor.fetchone():
                        cursor.execute("""
                            SELECT column_name FROM information_schema.columns
                            WHERE table_schema = %s AND table_name = 'crm_vendas_config'
                            AND column_name = 'proposta_conteudo_padrao'
                        """, [schema_name])
                        if cursor.fetchone():
                            self.stdout.write(self.style.SUCCESS('  proposta_conteudo_padrao já existe'))
                        else:
                            cursor.execute(
                                f'ALTER TABLE "{schema_name}"."crm_vendas_config" '
                                "ADD COLUMN proposta_conteudo_padrao TEXT DEFAULT ''"
                            )
                            self.stdout.write(self.style.SUCCESS('  proposta_conteudo_padrao adicionada'))
                    else:
                        self.stdout.write(self.style.WARNING('  Tabela crm_vendas_config não existe'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  proposta_conteudo_padrao: {e}'))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ Concluído. Teste acessar a loja novamente.'))
        self.stdout.write('='*60 + '\n')
