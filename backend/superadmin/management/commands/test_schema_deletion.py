"""
Comando para testar a exclusão automática de schema PostgreSQL

Este comando cria uma loja de teste, verifica se o schema foi criado,
exclui a loja e verifica se o schema foi removido automaticamente.

Uso:
    python manage.py test_schema_deletion
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth.models import User
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
import os


class Command(BaseCommand):
    help = 'Testa a exclusão automática de schema PostgreSQL ao deletar loja'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('TESTE: Exclusão Automática de Schema PostgreSQL'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))

        # Verificar se está usando PostgreSQL
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if 'postgres' not in DATABASE_URL.lower():
            self.stdout.write(self.style.ERROR('❌ Este teste só funciona com PostgreSQL'))
            self.stdout.write(self.style.WARNING('   Ambiente atual: SQLite (desenvolvimento)'))
            return

        self.stdout.write(self.style.SUCCESS('✅ Ambiente: PostgreSQL (produção)'))
        self.stdout.write('')

        # 1. Criar loja de teste
        self.stdout.write(self.style.WARNING('ETAPA 1: Criando loja de teste...'))
        
        try:
            # Buscar tipo de loja e plano
            tipo_loja = TipoLoja.objects.first()
            plano = PlanoAssinatura.objects.first()
            
            if not tipo_loja or not plano:
                self.stdout.write(self.style.ERROR('❌ Tipo de loja ou plano não encontrado'))
                return

            # Criar usuário de teste
            username = f'test_schema_deletion_{os.getpid()}'
            user = User.objects.create_user(
                username=username,
                email=f'{username}@test.com',
                password='test123'
            )
            self.stdout.write(self.style.SUCCESS(f'   ✅ Usuário criado: {username}'))

            # Criar loja de teste
            loja = Loja.objects.create(
                nome=f'Loja Teste Schema Deletion',
                slug=f'test-schema-{os.getpid()}',
                tipo_loja=tipo_loja,
                plano=plano,
                owner=user,
                database_name=f'loja_test_schema_{os.getpid()}',
                database_created=True
            )
            self.stdout.write(self.style.SUCCESS(f'   ✅ Loja criada: {loja.nome}'))
            self.stdout.write(self.style.SUCCESS(f'   ✅ Schema: {loja.database_name}'))
            self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar loja: {e}'))
            return

        # 2. Criar schema PostgreSQL
        self.stdout.write(self.style.WARNING('ETAPA 2: Criando schema PostgreSQL...'))
        
        try:
            schema_name = loja.database_name.replace('-', '_')
            
            with connection.cursor() as cursor:
                # Criar schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                self.stdout.write(self.style.SUCCESS(f'   ✅ Schema criado: {schema_name}'))
                
                # Criar tabela de teste no schema
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{schema_name}".test_table (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(100)
                    )
                ''')
                self.stdout.write(self.style.SUCCESS(f'   ✅ Tabela de teste criada'))
                
                # Inserir dados de teste
                cursor.execute(f'''
                    INSERT INTO "{schema_name}".test_table (nome) 
                    VALUES ('Teste 1'), ('Teste 2'), ('Teste 3')
                ''')
                self.stdout.write(self.style.SUCCESS(f'   ✅ Dados de teste inseridos'))
                
                # Verificar que schema existe
                cursor.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    [schema_name]
                )
                schema_exists = cursor.fetchone()
                
                if schema_exists:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Schema confirmado no PostgreSQL'))
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Schema não encontrado'))
                    return
            
            self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao criar schema: {e}'))
            return

        # 3. Excluir loja
        self.stdout.write(self.style.WARNING('ETAPA 3: Excluindo loja...'))
        
        try:
            loja_id = loja.id
            loja_nome = loja.nome
            
            # Excluir loja (signal pre_delete deve remover o schema)
            loja.delete()
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Loja excluída: {loja_nome} (ID: {loja_id})'))
            self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao excluir loja: {e}'))
            return

        # 4. Verificar se schema foi removido
        self.stdout.write(self.style.WARNING('ETAPA 4: Verificando remoção do schema...'))
        
        try:
            with connection.cursor() as cursor:
                # Verificar se schema ainda existe
                cursor.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                    [schema_name]
                )
                schema_exists = cursor.fetchone()
                
                if schema_exists:
                    self.stdout.write(self.style.ERROR(f'   ❌ FALHA: Schema ainda existe: {schema_name}'))
                    self.stdout.write(self.style.ERROR(f'   ❌ Signal pre_delete NÃO removeu o schema'))
                    
                    # Limpar manualmente
                    self.stdout.write(self.style.WARNING(f'   🧹 Limpando schema manualmente...'))
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Schema removido manualmente'))
                    
                    return
                else:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ SUCESSO: Schema foi removido automaticamente'))
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Signal pre_delete funcionou corretamente'))
            
            self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar schema: {e}'))
            return

        # 5. Limpar usuário de teste
        self.stdout.write(self.style.WARNING('ETAPA 5: Limpando dados de teste...'))
        
        try:
            user.delete()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Usuário de teste removido'))
            self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Erro ao remover usuário: {e}'))

        # Resultado final
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('✅ TESTE CONCLUÍDO COM SUCESSO'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('Resultado:'))
        self.stdout.write(self.style.SUCCESS('  ✅ Loja criada'))
        self.stdout.write(self.style.SUCCESS('  ✅ Schema PostgreSQL criado'))
        self.stdout.write(self.style.SUCCESS('  ✅ Loja excluída'))
        self.stdout.write(self.style.SUCCESS('  ✅ Schema PostgreSQL removido automaticamente'))
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('Conclusão: Signal pre_delete está funcionando corretamente!'))
        self.stdout.write(self.style.SUCCESS(''))
