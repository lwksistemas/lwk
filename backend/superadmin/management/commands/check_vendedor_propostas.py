from django.core.management.base import BaseCommand
from superadmin.models import Loja, VendedorUsuario
from crm_vendas.models import Proposta


class Command(BaseCommand):
    help = 'Verifica vendedores e propostas de uma loja'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Slug da loja')

    def handle(self, *args, **options):
        slug = options['slug']
        
        try:
            loja = Loja.objects.get(slug=slug)
            self.stdout.write(f'Loja: {loja.nome}')
            self.stdout.write(f'Owner: {loja.owner.username} (ID: {loja.owner.id})')
            self.stdout.write('')

            # Verificar vendedores
            vendedores = VendedorUsuario.objects.filter(loja=loja)
            self.stdout.write(f'Vendedores cadastrados: {vendedores.count()}')
            for v in vendedores:
                self.stdout.write(f'  - {v.user.username} (ID: {v.id}, Admin: {v.is_admin}, Ativo: {v.is_active})')
            self.stdout.write('')

            # Verificar propostas
            propostas = Proposta.objects.filter(loja=loja)
            self.stdout.write(f'Propostas cadastradas: {propostas.count()}')
            for p in propostas[:10]:
                vendedor_nome = p.vendedor.user.username if p.vendedor else "Sem vendedor"
                cliente_nome = p.cliente.nome if p.cliente else "Sem cliente"
                self.stdout.write(f'  - Proposta #{p.numero} - Cliente: {cliente_nome} - Vendedor: {vendedor_nome}')
                
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada'))
