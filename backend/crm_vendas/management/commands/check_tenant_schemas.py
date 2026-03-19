"""
Comando para verificar schemas de tenant no banco de dados.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Verifica schemas de tenant no banco de dados'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Verificando schemas de tenant...\n')
        
        # Listar schemas existentes
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name;
            """)
            schemas = cursor.fetchall()
            
            self.stdout.write(f'📊 Schemas existentes: {len(schemas)}')
            for schema in schemas:
                self.stdout.write(f'  - {schema[0]}')
        
        self.stdout.write('')
        
        # Listar lojas ativas
        lojas = Loja.objects.using('default').filter(is_active=True)
        self.stdout.write(f'📊 Lojas ativas: {lojas.count()}')
        for loja in lojas:
            schema_esperado = f'loja_{loja.id}'
            schema_existe = schema_esperado in [s[0] for s in schemas]
            status = '✅' if schema_existe else '❌'
            self.stdout.write(f'  {status} ID: {loja.id}, Nome: {loja.nome}, Schema: {schema_esperado}')
        
        self.stdout.write('')
        
        # Verificar se tabela AssinaturaDigital existe em cada schema
        self.stdout.write('📊 Verificando tabela crm_vendas_assinatura_digital:')
        for schema in schemas:
            schema_name = schema[0]
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = '{schema_name}'
                        AND table_name = 'crm_vendas_assinatura_digital'
                    );
                """)
                tabela_existe = cursor.fetchone()[0]
                status = '✅' if tabela_existe else '❌'
                self.stdout.write(f'  {status} {schema_name}')
