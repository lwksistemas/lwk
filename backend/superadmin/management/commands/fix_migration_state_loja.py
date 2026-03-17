"""
Corrige estado inconsistente de migrations em schema de loja.
Remove registros de migrations que causam "applied before its dependency".

Uso:
  heroku run "cd backend && python manage.py fix_migration_state_loja felix-5889" --app lwksistemas
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Corrige estado de migrations inconsistente no schema da loja'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug da loja (ex: felix-5889)')

    def handle(self, *args, **options):
        slug = options['slug'].strip()
        loja = Loja.objects.filter(slug__iexact=slug).first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'❌ Loja com slug "{slug}" não encontrada'))
            return

        schema_name = loja.database_name.replace('-', '_')
        self.stdout.write(f'Loja: {loja.nome} (ID: {loja.id})')
        self.stdout.write(f'Schema: {schema_name}\n')

        from django.conf import settings
        from core.db_config import ensure_loja_database_config
        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            self.stdout.write(self.style.ERROR('❌ Não foi possível configurar banco (verifique DATABASE_URL)'))
            return

        from django.db import connections
        conn = connections[loja.database_name]

        try:
            with conn.cursor() as cursor:
                # Verificar se django_migrations existe no schema
                cursor.execute("""
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'django_migrations'
                """, [schema_name])
                if not cursor.fetchone():
                    self.stdout.write(self.style.WARNING('⚠️ Tabela django_migrations não existe no schema'))
                    return

                # Remover migration problemática (servicos.0005 que depende de stores.0001)
                cursor.execute("""
                    DELETE FROM django_migrations
                    WHERE app = 'servicos' AND name = '0005_add_loja_isolation'
                """)
                deleted = cursor.rowcount
                if deleted:
                    self.stdout.write(self.style.SUCCESS(f'✅ Removido {deleted} registro(s) de servicos.0005_add_loja_isolation'))
                else:
                    self.stdout.write('  (Nenhum registro servicos.0005 encontrado)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {e}'))
            return
        finally:
            if loja.database_name in connections:
                try:
                    connections[loja.database_name].close()
                except Exception:
                    pass
            if loja.database_name in settings.DATABASES:
                del settings.DATABASES[loja.database_name]

        self.stdout.write(self.style.SUCCESS('\n✅ Concluído. Execute setup_loja_schema para reaplicar migrations.'))
