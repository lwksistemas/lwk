"""
Comando para restaurar vendedor removido por engano.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Restaura vendedor removido'

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
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO "{db_name}".crm_vendas_vendedor 
                (nome, email, telefone, cargo, comissao_padrao, is_admin, is_active, created_at, updated_at, loja_id)
                VALUES 
                ('Luiz Henrique Felix', 'consultorluizfelix@hotmail.com', '16 98140 2966', 'Vendedor', 0, false, true, NOW(), NOW(), %s)
            """, [loja.id])
            
            self.stdout.write(self.style.SUCCESS('✓ Vendedor restaurado com sucesso'))
