"""
Comando para analisar o sistema e identificar dados órfãos
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Analisa o sistema para identificar schemas órfãos, lojas sem schema e schemas vazios'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('ANÁLISE DE SCHEMAS E LOJAS'))
        self.stdout.write('='*60)
        
        # 1. Listar todos os schemas no PostgreSQL
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%' 
                ORDER BY schema_name
            """)
            schemas_db = [r[0] for r in cursor.fetchall()]
        
        self.stdout.write(f'\n📊 Schemas no PostgreSQL: {len(schemas_db)}')
        for s in schemas_db:
            self.stdout.write(f'  - {s}')
        
        # 2. Listar todas as lojas no Django
        lojas = Loja.objects.all().values('id', 'nome', 'slug', 'database_name', 'database_created', 'is_active')
        lojas_list = list(lojas)
        
        self.stdout.write(f'\n📊 Lojas no Django: {len(lojas_list)}')
        for loja in lojas_list:
            schema = loja['database_name'].replace('-', '_')
            status = '✅' if loja['is_active'] else '❌'
            db_created = '✅' if loja['database_created'] else '❌'
            self.stdout.write(f'  {status} ID:{loja["id"]:2d} | {loja["slug"]:20s} | DB:{db_created} | Schema: {schema}')
        
        # 3. Identificar schemas órfãos (no DB mas sem loja)
        schemas_esperados = [loja['database_name'].replace('-', '_') for loja in lojas_list]
        schemas_orfaos = [s for s in schemas_db if s not in schemas_esperados]
        
        self.stdout.write(f'\n⚠️  Schemas ÓRFÃOS (no DB mas sem loja): {len(schemas_orfaos)}')
        for s in schemas_orfaos:
            self.stdout.write(self.style.WARNING(f'  - {s}'))
        
        # 4. Identificar lojas sem schema (loja existe mas schema não)
        lojas_sem_schema = []
        for loja in lojas_list:
            schema = loja['database_name'].replace('-', '_')
            if schema not in schemas_db:
                lojas_sem_schema.append(loja)
        
        self.stdout.write(f'\n⚠️  Lojas SEM SCHEMA (loja existe mas schema não): {len(lojas_sem_schema)}')
        for loja in lojas_sem_schema:
            schema = loja['database_name'].replace('-', '_')
            self.stdout.write(self.style.WARNING(f'  - ID:{loja["id"]} | {loja["slug"]} | Schema esperado: {schema}'))
        
        # 5. Verificar schemas vazios (sem tabelas)
        self.stdout.write(f'\n📊 Verificando tabelas em cada schema...')
        schemas_vazios = []
        with connection.cursor() as cursor:
            for schema in schemas_db:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, [schema])
                count = cursor.fetchone()[0]
                
                if count == 0:
                    schemas_vazios.append(schema)
                    self.stdout.write(self.style.WARNING(f'  ⚠️  {schema}: 0 tabelas (VAZIO)'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ {schema}: {count} tabelas'))
        
        self.stdout.write(f'\n⚠️  Schemas VAZIOS (sem tabelas): {len(schemas_vazios)}')
        for s in schemas_vazios:
            self.stdout.write(self.style.WARNING(f'  - {s}'))
        
        # 6. Resumo
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS('RESUMO DA ANÁLISE'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total de schemas no PostgreSQL: {len(schemas_db)}')
        self.stdout.write(f'Total de lojas no Django: {len(lojas_list)}')
        self.stdout.write(self.style.WARNING(f'Schemas órfãos (sem loja): {len(schemas_orfaos)}'))
        self.stdout.write(self.style.WARNING(f'Lojas sem schema: {len(lojas_sem_schema)}'))
        self.stdout.write(self.style.WARNING(f'Schemas vazios (sem tabelas): {len(schemas_vazios)}'))
        self.stdout.write('='*60)
        
        # 7. Recomendações
        if schemas_orfaos or lojas_sem_schema or schemas_vazios:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.WARNING('RECOMENDAÇÕES'))
            self.stdout.write('='*60)
            
            if schemas_orfaos:
                self.stdout.write(self.style.WARNING(f'\n⚠️  {len(schemas_orfaos)} schema(s) órfão(s) encontrado(s)'))
                self.stdout.write('Ação recomendada: Excluir schemas órfãos para liberar espaço')
                self.stdout.write('Comando: python manage.py limpar_schemas_orfaos')
            
            if lojas_sem_schema:
                self.stdout.write(self.style.WARNING(f'\n⚠️  {len(lojas_sem_schema)} loja(s) sem schema encontrada(s)'))
                self.stdout.write('Ação recomendada: Excluir lojas inválidas ou recriar schemas')
                self.stdout.write('Essas lojas não funcionam e devem ser excluídas')
            
            if schemas_vazios:
                self.stdout.write(self.style.WARNING(f'\n⚠️  {len(schemas_vazios)} schema(s) vazio(s) encontrado(s)'))
                self.stdout.write('Ação recomendada: Aplicar migrations ou excluir schemas vazios')
                self.stdout.write('Comando: python manage.py verificar_schema_loja <loja_id> --fix')
        else:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.SUCCESS('✅ SISTEMA OK - Nenhum problema encontrado!'))
            self.stdout.write('='*60)
