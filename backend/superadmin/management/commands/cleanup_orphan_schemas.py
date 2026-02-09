"""
Comando para limpar schemas órfãos do PostgreSQL

Remove schemas que não têm loja correspondente no banco de dados
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Remove schemas órfãos do PostgreSQL (schemas sem loja correspondente)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria removido, sem remover',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Remove os schemas sem confirmação',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.WARNING('🔍 Analisando schemas do PostgreSQL...'))
        
        # Buscar todos os schemas que começam com 'loja_'
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%' 
                AND schema_name != 'loja_template'
                ORDER BY schema_name
            """)
            all_schemas = [row[0] for row in cursor.fetchall()]
        
        self.stdout.write(f'📊 Total de schemas encontrados: {len(all_schemas)}')
        
        # Buscar todos os database_name das lojas ativas
        lojas = Loja.objects.filter(is_active=True)
        lojas_database_names = set(loja.database_name.replace('-', '_') for loja in lojas)
        
        self.stdout.write(f'🏪 Total de lojas ativas: {lojas.count()}')
        self.stdout.write(f'📋 Database names das lojas: {sorted(lojas_database_names)}')
        
        # Identificar schemas órfãos
        orphan_schemas = []
        for schema in all_schemas:
            if schema not in lojas_database_names:
                orphan_schemas.append(schema)
        
        if not orphan_schemas:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum schema órfão encontrado!'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n⚠️  Encontrados {len(orphan_schemas)} schemas órfãos:'))
        for schema in orphan_schemas:
            self.stdout.write(f'  - {schema}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 Modo DRY-RUN: Nenhum schema foi removido'))
            self.stdout.write('Execute sem --dry-run para remover os schemas')
            return
        
        # Confirmar remoção
        if not force:
            self.stdout.write(self.style.WARNING(f'\n⚠️  ATENÇÃO: Isso vai DELETAR {len(orphan_schemas)} schemas permanentemente!'))
            confirm = input('Digite "CONFIRMAR" para continuar: ')
            if confirm != 'CONFIRMAR':
                self.stdout.write(self.style.ERROR('❌ Operação cancelada'))
                return
        
        # Remover schemas órfãos
        self.stdout.write(self.style.WARNING('\n🗑️  Removendo schemas órfãos...'))
        removed_count = 0
        
        with connection.cursor() as cursor:
            for schema in orphan_schemas:
                try:
                    self.stdout.write(f'  Removendo {schema}...', ending='')
                    cursor.execute(f'DROP SCHEMA IF EXISTS {schema} CASCADE')
                    removed_count += 1
                    self.stdout.write(self.style.SUCCESS(' ✅'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f' ❌ Erro: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ {removed_count} schemas removidos com sucesso!'))
        
        # Mostrar estatísticas finais
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name
            """)
            remaining_schemas = cursor.fetchall()
        
        self.stdout.write(f'\n📊 Schemas restantes: {len(remaining_schemas)}')
        self.stdout.write(f'🏪 Lojas ativas: {lojas.count()}')
