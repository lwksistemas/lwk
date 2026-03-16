"""
Adiciona coluna cpf_cnpj em crm_vendas_lead em schemas que não a possuem.
Corrige erro 500 "column cpf_cnpj does not exist" em lojas CRM.

Uso: heroku run "cd backend && python manage.py add_cpf_cnpj_lead_schemas" --app lwksistemas
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona coluna cpf_cnpj em crm_vendas_lead nos schemas CRM que não a possuem'

    def handle(self, *args, **options):
        tipo_crm = None
        try:
            from superadmin.models import TipoLoja
            tipo_crm = TipoLoja.objects.filter(slug='crm-vendas').first()
        except Exception:
            pass

        if not tipo_crm:
            self.stdout.write(self.style.WARNING('Tipo CRM Vendas não encontrado'))
            return

        lojas = Loja.objects.filter(tipo_loja=tipo_crm, is_active=True, database_created=True)
        self.stdout.write(f'Lojas CRM: {lojas.count()}\n')

        for loja in lojas:
            schema = loja.database_name.replace('-', '_')
            self.stdout.write(f'  Verificando {loja.nome} (schema: {schema})...')
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = 'crm_vendas_lead'
                    """, [schema])
                    if not cursor.fetchone():
                        self.stdout.write(self.style.WARNING(f'    ⚠️ Tabela crm_vendas_lead não existe'))
                        continue

                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = 'crm_vendas_lead' AND column_name = 'cpf_cnpj'
                    """, [schema])
                    if cursor.fetchone():
                        self.stdout.write(self.style.SUCCESS(f'    ✅ cpf_cnpj já existe'))
                        continue

                    cursor.execute(
                        'ALTER TABLE "{}"."crm_vendas_lead" ADD COLUMN IF NOT EXISTS cpf_cnpj VARCHAR(18) DEFAULT \'\''.format(schema)
                    )
                    self.stdout.write(self.style.SUCCESS(f'    ✅ Coluna cpf_cnpj adicionada'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Erro: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Concluído'))
