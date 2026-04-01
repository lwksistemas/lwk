"""
Comando para aplicar migrations no schema 'suporte' usando o método correto.
"""
from django.core.management.base import BaseCommand
from django.db import connection, connections
from django.conf import settings
from io import StringIO
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Aplica migrations no schema suporte'

    def handle(self, *args, **options):
        schema_name = 'suporte'
        
        self.stdout.write(f'🔍 Verificando schema {schema_name}...')
        
        # Verificar se schema existe
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT 1 FROM information_schema.schemata WHERE schema_name = %s',
                [schema_name]
            )
            existe = cursor.fetchone() is not None
        
        if not existe:
            self.stdout.write(self.style.ERROR(f'❌ Schema {schema_name} não existe!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Schema {schema_name} existe'))
        
        # Aplicar migrations do app suporte
        self.stdout.write(f'\n📦 Aplicando migrations do app suporte no schema {schema_name}...')
        
        try:
            # Criar tabela django_migrations se não existir
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO {schema_name}, public')
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS django_migrations (
                        id SERIAL PRIMARY KEY,
                        app VARCHAR(255) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        applied TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
            
            # Obter migrations do app suporte
            from django.db.migrations.loader import MigrationLoader
            loader = MigrationLoader(connection)
            
            # Verificar migrations já aplicadas
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO {schema_name}, public')
                cursor.execute("SELECT name FROM django_migrations WHERE app = 'suporte'")
                applied = {row[0] for row in cursor.fetchall()}
            
            self.stdout.write(f'  ℹ️  {len(applied)} migration(s) já aplicada(s)')
            
            # Obter todas as migrations do app suporte
            app_migrations = [
                key for key in loader.graph.nodes 
                if key[0] == 'suporte' and key[1] not in applied
            ]
            
            if not app_migrations:
                self.stdout.write(self.style.SUCCESS('  ✅ Todas as migrations já estão aplicadas!'))
            else:
                self.stdout.write(f'  📝 {len(app_migrations)} migration(s) pendente(s)')
                
                # Ordenar migrations
                app_migrations = sorted(app_migrations, key=lambda x: x[1])
                
                # Aplicar cada migration
                for app_label, migration_name in app_migrations:
                    try:
                        self.stdout.write(f'    🔄 Aplicando {migration_name}...')
                        
                        # Obter SQL da migration
                        sql_out = StringIO()
                        call_command(
                            'sqlmigrate',
                            app_label,
                            migration_name,
                            stdout=sql_out
                        )
                        sql = sql_out.getvalue()
                        
                        if sql and sql.strip() and sql.strip() != '--':
                            # Executar SQL no schema suporte
                            with connection.cursor() as cursor:
                                cursor.execute(f'SET search_path TO {schema_name}, public')
                                cursor.execute(sql)
                            
                            # Registrar migration
                            with connection.cursor() as cursor:
                                cursor.execute(f'SET search_path TO {schema_name}, public')
                                cursor.execute(
                                    "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
                                    [app_label, migration_name]
                                )
                            
                            self.stdout.write(self.style.SUCCESS(f'      ✅ {migration_name} aplicada'))
                        else:
                            self.stdout.write(self.style.WARNING(f'      ⚠️  {migration_name} - sem SQL'))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'      ❌ Erro: {e}'))
                        logger.exception(f'Erro ao aplicar migration {migration_name}')
            
            # Verificar tabelas criadas
            self.stdout.write(f'\n📊 Verificando tabelas no schema {schema_name}...')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, [schema_name])
                
                tabelas = cursor.fetchall()
                
                if tabelas:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ {len(tabelas)} tabela(s) encontrada(s):'))
                    for tabela in tabelas:
                        self.stdout.write(f'  - {tabela[0]}')
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Nenhuma tabela encontrada'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Migrations aplicadas com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro: {e}'))
            logger.exception('Erro ao aplicar migrations no schema suporte')
