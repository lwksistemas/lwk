"""
Comando para verificar se as tabelas existem no schema de uma loja específica
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Verifica se as tabelas existem no schema de uma loja específica'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            required=True,
            help='ID da loja',
        )

    def handle(self, *args, **options):
        loja_id = options['loja_id']

        self.stdout.write('\n' + '='*100)
        self.stdout.write('🔍 VERIFICAÇÃO DE TABELAS DA LOJA')
        self.stdout.write('='*100 + '\n')

        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Loja com ID {loja_id} não encontrada'))
            return

        self.stdout.write(f'🏪 Loja: {loja.nome}')
        self.stdout.write(f'   ID: {loja.id}')
        self.stdout.write(f'   Database: {loja.database_name}')
        self.stdout.write(f'   Tipo: {loja.tipo_loja.nome if loja.tipo_loja else "N/A"}')

        # Converter database_name para schema_name
        schema_name = loja.database_name.replace('-', '_')
        self.stdout.write(f'   Schema: {schema_name}\n')

        # Verificar se o schema existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            schema_exists = cursor.fetchone()

            if not schema_exists:
                self.stdout.write(self.style.ERROR(f'❌ Schema {schema_name} NÃO existe no PostgreSQL'))
                return

            self.stdout.write(self.style.SUCCESS(f'✅ Schema {schema_name} existe'))

            # Listar todas as tabelas do schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, [schema_name])
            
            tabelas = cursor.fetchall()

            if not tabelas:
                self.stdout.write(self.style.ERROR(f'\n❌ NENHUMA TABELA encontrada no schema {schema_name}'))
                self.stdout.write('\n⚠️  O schema existe mas está VAZIO!')
                self.stdout.write('   Execute: python manage.py criar_tabelas_lojas --loja-id ' + str(loja_id))
            else:
                self.stdout.write(self.style.SUCCESS(f'\n✅ {len(tabelas)} tabelas encontradas:'))
                for tabela in tabelas:
                    self.stdout.write(f'   - {tabela[0]}')

                # Verificar tabelas específicas importantes
                tabelas_importantes = [
                    'clinica_clientes',
                    'clinica_profissionais',
                    'clinica_procedimentos',
                    'clinica_agendamentos',
                    'clinica_funcionarios'
                ]

                self.stdout.write('\n📋 Verificando tabelas importantes:')
                tabelas_nomes = [t[0] for t in tabelas]
                
                for tabela in tabelas_importantes:
                    if tabela in tabelas_nomes:
                        # Contar registros
                        cursor.execute(f'SELECT COUNT(*) FROM {schema_name}.{tabela}')
                        count = cursor.fetchone()[0]
                        self.stdout.write(f'   ✅ {tabela}: {count} registros')
                    else:
                        self.stdout.write(self.style.ERROR(f'   ❌ {tabela}: NÃO EXISTE'))

        self.stdout.write('\n' + '='*100)
        self.stdout.write('✅ Verificação concluída!')
        self.stdout.write('='*100 + '\n')
