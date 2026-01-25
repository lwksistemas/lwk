"""
Comando para criar dados iniciais do sistema
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import TipoLoja, PlanoAssinatura
from decimal import Decimal


class Command(BaseCommand):
    help = 'Cria dados iniciais do sistema (tipos de loja e planos)'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando setup de dados iniciais...\n')
        
        # Criar superusuário se não existir
        self.create_superuser()
        
        # Criar tipos de loja
        self.create_tipos_loja()
        
        # Criar planos
        self.create_planos()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Setup concluído com sucesso!'))

    def create_superuser(self):
        """Cria superusuário padrão"""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@lwksistemas.com.br',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('✅ Superusuário criado: admin/admin123'))
        else:
            self.stdout.write('ℹ️  Superusuário já existe')

    def create_tipos_loja(self):
        """Cria tipos de loja padrão"""
        tipos = [
            {
                'nome': 'Clínica de Estética',
                'slug': 'clinica-estetica',
                'descricao': 'Sistema completo para clínicas de estética com agendamentos, prontuários e controle financeiro',
                'icone': '💆',
                'cor': '#FF6B9D',
                'is_active': True
            },
            {
                'nome': 'CRM Vendas',
                'slug': 'crm-vendas',
                'descricao': 'Sistema de CRM para gestão de vendas, leads e pipeline comercial',
                'icone': '📊',
                'cor': '#4CAF50',
                'is_active': True
            },
            {
                'nome': 'E-commerce',
                'slug': 'ecommerce',
                'descricao': 'Loja virtual completa com catálogo de produtos, carrinho e pagamentos',
                'icone': '🛒',
                'cor': '#2196F3',
                'is_active': True
            },
            {
                'nome': 'Restaurante',
                'slug': 'restaurante',
                'descricao': 'Sistema para restaurantes com cardápio digital, pedidos e delivery',
                'icone': '🍽️',
                'cor': '#FF9800',
                'is_active': True
            },
            {
                'nome': 'Serviços',
                'slug': 'servicos',
                'descricao': 'Sistema para prestadores de serviços com agendamentos e orçamentos',
                'icone': '🔧',
                'cor': '#9C27B0',
                'is_active': True
            }
        ]
        
        created_count = 0
        for tipo_data in tipos:
            tipo, created = TipoLoja.objects.get_or_create(
                slug=tipo_data['slug'],
                defaults=tipo_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Tipo criado: {tipo.nome}')
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ {created_count} tipos de loja criados'))
        else:
            self.stdout.write('ℹ️  Tipos de loja já existem')

    def create_planos(self):
        """Cria planos de assinatura padrão"""
        # Buscar tipos de loja
        tipos = {tipo.slug: tipo for tipo in TipoLoja.objects.all()}
        
        planos = [
            # Planos Clínica de Estética
            {
                'nome': 'Básico Clínica',
                'slug': 'basico-clinica',
                'tipo_loja': tipos.get('clinica-estetica'),
                'descricao': 'Plano básico para clínicas pequenas',
                'preco_mensal': Decimal('99.90'),
                'preco_anual': Decimal('999.00'),
                'max_usuarios': 3,
                'max_produtos': 50,
                'recursos': {
                    'agendamentos': True,
                    'prontuarios': True,
                    'financeiro': True,
                    'relatorios': False,
                    'api': False
                },
                'is_active': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional Clínica',
                'slug': 'profissional-clinica',
                'tipo_loja': tipos.get('clinica-estetica'),
                'descricao': 'Plano completo para clínicas médias',
                'preco_mensal': Decimal('199.90'),
                'preco_anual': Decimal('1999.00'),
                'max_usuarios': 10,
                'max_produtos': 200,
                'recursos': {
                    'agendamentos': True,
                    'prontuarios': True,
                    'financeiro': True,
                    'relatorios': True,
                    'api': False
                },
                'is_active': True,
                'ordem': 2
            },
            # Planos CRM
            {
                'nome': 'Básico CRM',
                'slug': 'basico-crm',
                'tipo_loja': tipos.get('crm-vendas'),
                'descricao': 'Plano básico para pequenas equipes',
                'preco_mensal': Decimal('79.90'),
                'preco_anual': Decimal('799.00'),
                'max_usuarios': 5,
                'max_produtos': 100,
                'recursos': {
                    'leads': True,
                    'pipeline': True,
                    'relatorios': False,
                    'api': False
                },
                'is_active': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional CRM',
                'slug': 'profissional-crm',
                'tipo_loja': tipos.get('crm-vendas'),
                'descricao': 'Plano completo para equipes de vendas',
                'preco_mensal': Decimal('149.90'),
                'preco_anual': Decimal('1499.00'),
                'max_usuarios': 20,
                'max_produtos': 500,
                'recursos': {
                    'leads': True,
                    'pipeline': True,
                    'relatorios': True,
                    'api': True
                },
                'is_active': True,
                'ordem': 2
            },
            # Planos E-commerce
            {
                'nome': 'Básico E-commerce',
                'slug': 'basico-ecommerce',
                'tipo_loja': tipos.get('ecommerce'),
                'descricao': 'Plano básico para lojas pequenas',
                'preco_mensal': Decimal('89.90'),
                'preco_anual': Decimal('899.00'),
                'max_usuarios': 3,
                'max_produtos': 100,
                'recursos': {
                    'catalogo': True,
                    'carrinho': True,
                    'pagamentos': True,
                    'relatorios': False
                },
                'is_active': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional E-commerce',
                'slug': 'profissional-ecommerce',
                'tipo_loja': tipos.get('ecommerce'),
                'descricao': 'Plano completo para lojas médias',
                'preco_mensal': Decimal('179.90'),
                'preco_anual': Decimal('1799.00'),
                'max_usuarios': 10,
                'max_produtos': 1000,
                'recursos': {
                    'catalogo': True,
                    'carrinho': True,
                    'pagamentos': True,
                    'relatorios': True,
                    'api': True
                },
                'is_active': True,
                'ordem': 2
            },
            # Planos Restaurante
            {
                'nome': 'Básico Restaurante',
                'slug': 'basico-restaurante',
                'tipo_loja': tipos.get('restaurante'),
                'descricao': 'Plano básico para restaurantes pequenos',
                'preco_mensal': Decimal('69.90'),
                'preco_anual': Decimal('699.00'),
                'max_usuarios': 5,
                'max_produtos': 50,
                'recursos': {
                    'cardapio': True,
                    'pedidos': True,
                    'delivery': False
                },
                'is_active': True,
                'ordem': 1
            },
            # Planos Serviços
            {
                'nome': 'Básico Serviços',
                'slug': 'basico-servicos',
                'tipo_loja': tipos.get('servicos'),
                'descricao': 'Plano básico para prestadores de serviços',
                'preco_mensal': Decimal('59.90'),
                'preco_anual': Decimal('599.00'),
                'max_usuarios': 3,
                'max_produtos': 30,
                'recursos': {
                    'agendamentos': True,
                    'orcamentos': True,
                    'financeiro': True
                },
                'is_active': True,
                'ordem': 1
            }
        ]
        
        created_count = 0
        for plano_data in planos:
            if plano_data['tipo_loja']:  # Só criar se o tipo de loja existir
                plano, created = PlanoAssinatura.objects.get_or_create(
                    slug=plano_data['slug'],
                    defaults=plano_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✅ Plano criado: {plano.nome}')
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ {created_count} planos criados'))
        else:
            self.stdout.write('ℹ️  Planos já existem')
