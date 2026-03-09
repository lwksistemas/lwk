"""
Adiciona coluna vendedor_id em crm_vendas_lead e crm_vendas_conta
em schemas que têm as tabelas mas não têm a coluna.

Uso:
  python manage.py fix_vendedor_column
  heroku run "cd backend && python manage.py fix_vendedor_column" -a lwksistemas
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Adiciona vendedor_id em crm_vendas_lead e crm_vendas_conta nos schemas que precisam'

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write(self.style.WARNING('Apenas PostgreSQL suportado. Nada a fazer.'))
            return

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                AND schema_name NOT LIKE 'pg_%'
            """)
            schemas = [row[0] for row in cursor.fetchall()]

        fixed_lead = 0
        fixed_conta = 0
        for schema in schemas:
            safe_schema = schema.replace('"', '""')
            if not all(c.isalnum() or c == '_' for c in schema):
                continue

            with connection.cursor() as cursor:
                # Lead
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'crm_vendas_lead'
                """, [schema])
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = 'crm_vendas_lead'
                        AND column_name = 'vendedor_id'
                    """, [schema])
                    if not cursor.fetchone():
                        try:
                            cursor.execute(f'''
                                ALTER TABLE "{safe_schema}".crm_vendas_lead
                                ADD COLUMN vendedor_id INTEGER NULL
                                REFERENCES "{safe_schema}".crm_vendas_vendedor(id) ON DELETE SET NULL
                            ''')
                            self.stdout.write(self.style.SUCCESS(f'  ✅ {schema}: vendedor_id em lead'))
                            fixed_lead += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  ❌ {schema} lead: {e}'))
                # Conta
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'crm_vendas_conta'
                """, [schema])
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = 'crm_vendas_conta'
                        AND column_name = 'vendedor_id'
                    """, [schema])
                    if not cursor.fetchone():
                        try:
                            cursor.execute(f'''
                                ALTER TABLE "{safe_schema}".crm_vendas_conta
                                ADD COLUMN vendedor_id INTEGER NULL
                                REFERENCES "{safe_schema}".crm_vendas_vendedor(id) ON DELETE SET NULL
                            ''')
                            self.stdout.write(self.style.SUCCESS(f'  ✅ {schema}: vendedor_id em conta'))
                            fixed_conta += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  ❌ {schema} conta: {e}'))

        total = fixed_lead + fixed_conta
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Concluído: {total} coluna(s) adicionada(s) (lead: {fixed_lead}, conta: {fixed_conta})'
        ))
