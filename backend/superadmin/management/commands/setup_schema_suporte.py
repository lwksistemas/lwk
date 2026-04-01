"""
Comando para configurar o schema 'suporte' com todas as tabelas necessárias.
"""
from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Configura o schema suporte com as tabelas necessárias'

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
            self.stdout.write(self.style.WARNING(f'Schema {schema_name} não existe. Criando...'))
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
            self.stdout.write(self.style.SUCCESS(f'✅ Schema {schema_name} criado'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Schema {schema_name} já existe'))
        
        # Aplicar migrations no schema suporte
        self.stdout.write(f'📦 Aplicando migrations no schema {schema_name}...')
        
        # Apps que devem ter tabelas no schema suporte
        apps_suporte = ['suporte', 'auth', 'contenttypes', 'sessions']
        
        with connection.cursor() as cursor:
            # Definir search_path
            cursor.execute(f'SET search_path TO {schema_name}, public')
            
            # Criar tabela django_migrations se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_migrations (
                    id SERIAL PRIMARY KEY,
                    app VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            
            self.stdout.write('✅ Tabela django_migrations criada')
        
        # Executar migrations usando call_command
        from django.core.management import call_command
        from io import StringIO
        
        for app in apps_suporte:
            try:
                self.stdout.write(f'  📝 Aplicando migrations de {app}...')
                
                # Obter SQL das migrations
                sql_out = StringIO()
                try:
                    call_command('sqlmigrate', app, '0001', stdout=sql_out)
                    sql = sql_out.getvalue()
                    
                    if sql and sql.strip() != '--':
                        with connection.cursor() as cursor:
                            cursor.execute(f'SET search_path TO {schema_name}, public')
                            cursor.execute(sql)
                        self.stdout.write(self.style.SUCCESS(f'    ✅ {app} - migrations aplicadas'))
                    else:
                        self.stdout.write(self.style.WARNING(f'    ⚠️  {app} - sem SQL para aplicar'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'    ⚠️  {app} - erro: {e}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ❌ Erro em {app}: {e}'))
        
        # Verificar tabelas criadas
        self.stdout.write(f'\n📊 Verificando tabelas criadas no schema {schema_name}...')
        
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
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Setup do schema {schema_name} concluído!'))
