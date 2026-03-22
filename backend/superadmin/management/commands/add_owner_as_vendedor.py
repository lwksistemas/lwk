from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja, VendedorUsuario


class Command(BaseCommand):
    help = 'Adiciona o owner da loja como vendedor admin'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug da loja')

    def handle(self, *args, **options):
        slug = options['slug']
        
        try:
            loja = Loja.objects.get(slug=slug)
            owner = loja.owner
            
            self.stdout.write(f'Loja: {loja.nome}')
            self.stdout.write(f'Owner: {owner.username} (ID: {owner.id})')
            
            # Verificar se já existe VendedorUsuario
            vendedor_usuario_existente = VendedorUsuario.objects.filter(loja=loja, user=owner).first()
            
            if vendedor_usuario_existente:
                self.stdout.write(self.style.WARNING(f'Owner já tem VendedorUsuario (ID: {vendedor_usuario_existente.id}, vendedor_id: {vendedor_usuario_existente.vendedor_id})'))
                return
            
            # Conectar ao schema da loja
            schema_name = f'loja_{loja.slug}'
            
            with connection.cursor() as cursor:
                # Verificar se o schema existe
                cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [schema_name])
                if not cursor.fetchone():
                    self.stdout.write(self.style.ERROR(f'Schema {schema_name} não existe'))
                    return
                
                # Mudar para o schema da loja
                cursor.execute(f'SET search_path TO {schema_name}')
                
                # Verificar se já existe vendedor com este user_id
                cursor.execute('SELECT id, nome, is_admin FROM crm_vendas_vendedor WHERE user_id = %s', [owner.id])
                vendedor_row = cursor.fetchone()
                
                if vendedor_row:
                    vendedor_id, nome, is_admin = vendedor_row
                    self.stdout.write(self.style.WARNING(f'Vendedor já existe no schema (ID: {vendedor_id}, Nome: {nome}, Admin: {is_admin})'))
                    
                    # Criar VendedorUsuario
                    vendedor_usuario = VendedorUsuario.objects.create(
                        loja=loja,
                        user=owner,
                        vendedor_id=vendedor_id,
                        precisa_trocar_senha=False  # Owner já tem senha
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'✅ VendedorUsuario criado! (ID: {vendedor_usuario.id})'))
                    return
                
                # Criar vendedor no schema da loja
                cursor.execute('''
                    INSERT INTO crm_vendas_vendedor (nome, email, telefone, is_admin, is_active, user_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                ''', [
                    owner.get_full_name() or owner.username,
                    owner.email,
                    '',  # telefone vazio
                    True,  # is_admin
                    True,  # is_active
                    owner.id
                ])
                
                vendedor_id = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'✅ Vendedor criado no schema (ID: {vendedor_id})'))
            
            # Criar VendedorUsuario
            vendedor_usuario = VendedorUsuario.objects.create(
                loja=loja,
                user=owner,
                vendedor_id=vendedor_id,
                precisa_trocar_senha=False  # Owner já tem senha
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ VendedorUsuario criado! (ID: {vendedor_usuario.id})'))
            self.stdout.write(f'   - Vendedor ID no schema: {vendedor_id}')
            self.stdout.write(f'   - Precisa trocar senha: {vendedor_usuario.precisa_trocar_senha}')
                
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada'))
