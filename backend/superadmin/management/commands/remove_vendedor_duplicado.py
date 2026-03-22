"""
Comando para remover vendedor duplicado (vendedor antigo com is_admin=True).
Uso: python manage.py remove_vendedor_duplicado <slug_loja>
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Remove vendedor duplicado (is_admin=True antigo) de uma loja'

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
        owner_email = (loja.owner.email or '').strip().lower()
        
        self.stdout.write(f'Processando loja: {loja.nome} (DB: {db_name})')
        self.stdout.write(f'Email do owner: {owner_email}')

        with connection.cursor() as cursor:
            # Listar vendedores com mesmo email
            cursor.execute(f"""
                SELECT id, nome, email, is_admin, cargo
                FROM "{db_name}".crm_vendas_vendedor
                WHERE LOWER(email) = %s
                ORDER BY id
            """, [owner_email])
            
            vendedores = cursor.fetchall()
            
            if len(vendedores) <= 1:
                self.stdout.write(self.style.WARNING('Nenhum vendedor duplicado encontrado'))
                return
            
            self.stdout.write(f'\nEncontrados {len(vendedores)} vendedores com email {owner_email}:')
            for v in vendedores:
                self.stdout.write(f'  ID: {v[0]}, Nome: {v[1]}, is_admin: {v[3]}, Cargo: {v[4]}')
            
            # Remover o vendedor mais antigo (menor ID)
            vendedor_antigo_id = vendedores[0][0]  # Primeiro vendedor (menor ID)
            vendedor_novo_id = vendedores[1][0]  # Segundo vendedor (maior ID)
            
            self.stdout.write(f'\nAtualizando oportunidades do vendedor ID {vendedor_antigo_id} para ID {vendedor_novo_id}...')
            cursor.execute(f"""
                UPDATE "{db_name}".crm_vendas_oportunidade
                SET vendedor_id = %s
                WHERE vendedor_id = %s
            """, [vendedor_novo_id, vendedor_antigo_id])
            
            oportunidades_atualizadas = cursor.rowcount
            self.stdout.write(f'✓ {oportunidades_atualizadas} oportunidades atualizadas')
            
            self.stdout.write(f'\nRemovendo vendedor ID {vendedor_antigo_id}...')
            cursor.execute(f"""
                DELETE FROM "{db_name}".crm_vendas_vendedor
                WHERE id = %s
            """, [vendedor_antigo_id])
            
            self.stdout.write(self.style.SUCCESS(f'✓ Vendedor ID {vendedor_antigo_id} removido com sucesso'))
