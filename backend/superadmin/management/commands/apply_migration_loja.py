"""
Comando para aplicar migration específica em uma loja.
Uso: python manage.py apply_migration_loja <slug_loja>
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Aplica migration pendente em uma loja específica'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug da loja')

    def handle(self, *args, **options):
        slug = options['slug']
        
        try:
            loja = Loja.objects.using('default').get(slug=slug)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Loja {slug} não encontrada'))
            return

        db_name = f'loja_{slug}'
        self.stdout.write(f'Aplicando migration na loja: {loja.nome_fantasia} (DB: {db_name})')

        # Conectar ao banco da loja
        with connection.cursor() as cursor:
            # Verificar se a coluna já existe
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='crm_vendas_vendedor' 
                AND column_name='comissao_padrao'
                AND table_schema='{db_name}'
            """)
            
            if cursor.fetchone():
                self.stdout.write(self.style.WARNING('Coluna comissao_padrao já existe'))
                return

            # Adicionar a coluna
            self.stdout.write('Adicionando coluna comissao_padrao...')
            cursor.execute(f"""
                ALTER TABLE "{db_name}".crm_vendas_vendedor 
                ADD COLUMN comissao_padrao NUMERIC(5, 2) DEFAULT 0 NOT NULL
            """)
            
            self.stdout.write(self.style.SUCCESS('✓ Coluna comissao_padrao adicionada com sucesso'))

