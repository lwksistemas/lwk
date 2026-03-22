from django.core.management.base import BaseCommand
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
            
            # Verificar se já existe
            vendedor_existente = VendedorUsuario.objects.filter(loja=loja, user=owner).first()
            
            if vendedor_existente:
                self.stdout.write(self.style.WARNING(f'Owner já é vendedor (ID: {vendedor_existente.id})'))
                if not vendedor_existente.is_admin:
                    vendedor_existente.is_admin = True
                    vendedor_existente.save()
                    self.stdout.write(self.style.SUCCESS('✅ Atualizado para admin'))
                return
            
            # Criar vendedor
            vendedor = VendedorUsuario.objects.create(
                loja=loja,
                user=owner,
                is_admin=True,
                is_active=True,
                precisa_trocar_senha=False  # Owner já tem senha
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Vendedor criado com sucesso! (ID: {vendedor.id})'))
            self.stdout.write(f'   - Admin: {vendedor.is_admin}')
            self.stdout.write(f'   - Ativo: {vendedor.is_active}')
                
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada'))
