"""
Comando para verificar schemas das lojas
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Verifica se os schemas das lojas existem no PostgreSQL'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*100)
        self.stdout.write('🔍 VERIFICAÇÃO DE SCHEMAS NO POSTGRESQL')
        self.stdout.write('='*100 + '\n')

        # Listar todos os schemas
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name
            """)
            schemas_existentes = [row[0] for row in cursor.fetchall()]

        self.stdout.write(f'📊 Total de schemas "loja_*" no PostgreSQL: {len(schemas_existentes)}\n')
        
        if schemas_existentes:
            self.stdout.write('Schemas encontrados:')
            for schema in schemas_existentes:
                self.stdout.write(f'  - {schema}')
            self.stdout.write('')

        # Verificar lojas ativas
        lojas = Loja.objects.filter(is_active=True, tipo_loja__nome='Clínica de Estética').order_by('created_at')
        
        self.stdout.write(f'📊 Total de clínicas ativas: {lojas.count()}\n')
        self.stdout.write('Verificação de schemas por loja:')
        self.stdout.write('-' * 100)

        lojas_sem_schema = []
        
        for loja in lojas:
            schema_name = loja.database_name.replace('-', '_')
            tem_schema = schema_name in schemas_existentes
            
            status = '✅' if tem_schema else '❌'
            self.stdout.write(f'{status} ID: {loja.id:3d} | {loja.nome:35s} | Schema: {schema_name:35s}')
            
            if not tem_schema:
                lojas_sem_schema.append(loja)

        self.stdout.write('-' * 100)

        # Resumo
        if lojas_sem_schema:
            self.stdout.write(self.style.ERROR(f'\n❌ {len(lojas_sem_schema)} loja(s) SEM schema no PostgreSQL:'))
            for loja in lojas_sem_schema:
                self.stdout.write(f'   - {loja.nome} (ID: {loja.id}) - Criada em: {loja.created_at}')
            self.stdout.write(self.style.WARNING('\n⚠️  PROBLEMA: Lojas sem schema usam o schema "public" compartilhado!'))
            self.stdout.write(self.style.WARNING('⚠️  Por isso todas veem os mesmos dados!'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Todas as lojas têm schema no PostgreSQL'))

        self.stdout.write('\n' + '='*100 + '\n')
