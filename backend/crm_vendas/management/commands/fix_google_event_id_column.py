"""
Comando para adicionar coluna google_event_id em schemas que têm crm_vendas_atividade mas não têm a coluna.
Corrige: psycopg2.errors.UndefinedColumn: column "google_event_id" of relation "crm_vendas_atividade" does not exist

Uso:
  python manage.py fix_google_event_id_column
  heroku run "cd backend && python manage.py fix_google_event_id_column" -a lwksistemas
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Adiciona google_event_id em schemas com crm_vendas_atividade que não têm a coluna'

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

        fixed = 0
        skipped = 0
        for schema in schemas:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'crm_vendas_atividade'
                """, [schema])
                if not cursor.fetchone():
                    continue

                cursor.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = 'crm_vendas_atividade'
                    AND column_name = 'google_event_id'
                """, [schema])
                if cursor.fetchone():
                    skipped += 1
                    continue

                try:
                    if not all(c.isalnum() or c == '_' for c in schema):
                        self.stdout.write(self.style.WARNING(f'  ⚠️ {schema}: nome inválido, pulando'))
                        continue
                    cursor.execute(
                        'ALTER TABLE "{}".crm_vendas_atividade ADD COLUMN google_event_id VARCHAR(255) NULL'.format(
                            schema.replace('"', '""')
                        )
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✅ {schema}: coluna adicionada'))
                    fixed += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ❌ {schema}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Concluído: {fixed} schema(s) corrigido(s), {skipped} já tinham a coluna'))
