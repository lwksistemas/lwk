"""
Comando para criar dados iniciais do sistema
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import TipoLoja, PlanoAssinatura
from decimal import Decimal


class Command(BaseCommand):
    help = 'Cria dados iniciais do sistema (tipos de app e planos)'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando setup de dados iniciais...\n')
        
        # Criar superusuário se não existir
        self.create_superuser()
        
        # Criar tipos de app
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
        """Cria tipos de app padrão"""
        tipos = [
            {
                'nome': 'Clínica de Estética',
                'slug': 'clinica-estetica',
                'descricao': 'Sistema completo para clínicas de estética com agendamentos, prontuários e controle financeiro',
                'dashboard_template': 'clinica',
                'cor_primaria': '#FF6B9D',
                'cor_secundaria': '#FF4081',
                'tem_produtos': False,
                'tem_servicos': True,
                'tem_agendamento': True,
                'tem_delivery': False,
                'tem_estoque': False
            },
            {
                'nome': 'CRM Vendas',
                'slug': 'crm-vendas',
                'descricao': 'CRM para gestão de vendas, leads, pipeline e oportunidades',
                'dashboard_template': 'crm',
                'cor_primaria': '#4CAF50',
                'cor_secundaria': '#388E3C',
                'tem_produtos': True,
                'tem_servicos': True,
                'tem_agendamento': False,
                'tem_delivery': False,
                'tem_estoque': True
            },
            {
                'nome': 'E-commerce',
                'slug': 'ecommerce',
                'descricao': 'Loja virtual completa com catálogo de produtos, carrinho e pagamentos',
                'dashboard_template': 'ecommerce',
                'cor_primaria': '#2196F3',
                'cor_secundaria': '#1976D2',
                'tem_produtos': True,
                'tem_servicos': False,
                'tem_agendamento': False,
                'tem_delivery': True,
                'tem_estoque': True
            },
            {
                'nome': 'Restaurante',
                'slug': 'restaurante',
                'descricao': 'Sistema para restaurantes com cardápio digital, pedidos e delivery',
                'dashboard_template': 'restaurante',
                'cor_primaria': '#FF9800',
                'cor_secundaria': '#F57C00',
                'tem_produtos': True,
                'tem_servicos': False,
                'tem_agendamento': False,
                'tem_delivery': True,
                'tem_estoque': True
            },
            {
                'nome': 'Serviços',
                'slug': 'servicos',
                'descricao': 'Sistema para prestadores de serviços com agendamentos e orçamentos',
                'dashboard_template': 'servicos',
                'cor_primaria': '#9C27B0',
                'cor_secundaria': '#7B1FA2',
                'tem_produtos': False,
                'tem_servicos': True,
                'tem_agendamento': True,
                'tem_delivery': False,
                'tem_estoque': False
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
            self.stdout.write(self.style.SUCCESS(f'✅ {created_count} tipos de app criados'))
        else:
            self.stdout.write('ℹ️  Tipos de app já existem')

    def create_planos(self):
        """Cria planos de assinatura padrão"""
        # Buscar tipos de app
        tipos = {tipo.slug: tipo for tipo in TipoLoja.objects.all()}
        
        planos = [
            # Planos Clínica de Estética
            {
                'nome': 'Básico Clínica',
                'slug': 'basico-clinica',
                'tipo_slug': 'clinica-estetica',
                'descricao': 'Plano básico para clínicas pequenas',
                'preco_mensal': Decimal('99.90'),
                'preco_anual': Decimal('999.00'),
                'max_usuarios': 3,
                'max_produtos': 50,
                'max_pedidos_mes': 500,
                'espaco_storage_gb': 5,
                'tem_relatorios_avancados': False,
                'tem_api_acesso': False,
                'tem_suporte_prioritario': False,
                'tem_dominio_customizado': False,
                'tem_whatsapp_integration': False,
                'is_active': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional Clínica',
                'slug': 'profissional-clinica',
                'tipo_slug': 'clinica-estetica',
                'descricao': 'Plano completo para clínicas médias',
                'preco_mensal': Decimal('199.90'),
                'preco_anual': Decimal('1999.00'),
                'max_usuarios': 10,
                'max_produtos': 200,
                'max_pedidos_mes': 2000,
                'espaco_storage_gb': 20,
                'tem_relatorios_avancados': True,
                'tem_api_acesso': False,
                'tem_suporte_prioritario': True,
                'tem_dominio_customizado': True,
                'tem_whatsapp_integration': True,
                'is_active': True,
                'ordem': 2
            },
            # Planos CRM Vendas
            {
                'nome': 'Básico CRM',
                'slug': 'basico-crm',
                'tipo_slug': 'crm-vendas',
                'descricao': 'Plano básico para pequenas equipes de vendas',
                'preco_mensal': Decimal('79.90'),
                'preco_anual': Decimal('799.00'),
                'max_usuarios': 5,
                'max_produtos': 100,
                'max_pedidos_mes': 1000,
                'espaco_storage_gb': 5,
                'tem_relatorios_avancados': False,
                'tem_api_acesso': False,
                'tem_suporte_prioritario': False,
                'tem_dominio_customizado': False,
                'tem_whatsapp_integration': False,
                'is_active': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional CRM',
                'slug': 'profissional-crm',
                'tipo_slug': 'crm-vendas',
                'descricao': 'Plano completo para equipes de vendas',
                'preco_mensal': Decimal('149.90'),
                'preco_anual': Decimal('1499.00'),
                'max_usuarios': 20,
                'max_produtos': 500,
                'max_pedidos_mes': 5000,
                'espaco_storage_gb': 50,
                'tem_relatorios_avancados': True,
                'tem_api_acesso': True,
                'tem_suporte_prioritario': True,
                'tem_dominio_customizado': True,
                'tem_whatsapp_integration': True,
                'is_active': True,
                'ordem': 2
            },
            # Planos E-commerce
            {
                'nome': 'Básico E-commerce',
                'slug': 'basico-ecommerce',
                'tipo_slug': 'ecommerce',
                'descricao': 'Plano básico para lojas pequenas',
                'preco_mensal': Decimal('89.90'),
                'preco_anual': Decimal('899.00'),
                'max_usuarios': 3,
                'max_produtos': 100,
                'max_pedidos_mes': 500,
                'espaco_storage_gb': 10,
                'tem_relatorios_avancados': False,
                'tem_api_acesso': False,
                'tem_suporte_prioritario': False,
                'tem_dominio_customizado': False,
                'tem_whatsapp_integration': False,
                'is_active': True,
                'ordem': 1
            },
            {
                'nome': 'Profissional E-commerce',
                'slug': 'profissional-ecommerce',
                'tipo_slug': 'ecommerce',
                'descricao': 'Plano completo para lojas médias',
                'preco_mensal': Decimal('179.90'),
                'preco_anual': Decimal('1799.00'),
                'max_usuarios': 10,
                'max_produtos': 1000,
                'max_pedidos_mes': 5000,
                'espaco_storage_gb': 50,
                'tem_relatorios_avancados': True,
                'tem_api_acesso': True,
                'tem_suporte_prioritario': True,
                'tem_dominio_customizado': True,
                'tem_whatsapp_integration': True,
                'is_active': True,
                'ordem': 2
            },
            # Planos Restaurante
            {
                'nome': 'Básico Restaurante',
                'slug': 'basico-restaurante',
                'tipo_slug': 'restaurante',
                'descricao': 'Plano básico para restaurantes pequenos',
                'preco_mensal': Decimal('69.90'),
                'preco_anual': Decimal('699.00'),
                'max_usuarios': 5,
                'max_produtos': 50,
                'max_pedidos_mes': 1000,
                'espaco_storage_gb': 5,
                'tem_relatorios_avancados': False,
                'tem_api_acesso': False,
                'tem_suporte_prioritario': False,
                'tem_dominio_customizado': False,
                'tem_whatsapp_integration': True,
                'is_active': True,
                'ordem': 1
            },
            # Planos Serviços
            {
                'nome': 'Básico Serviços',
                'slug': 'basico-servicos',
                'tipo_slug': 'servicos',
                'descricao': 'Plano básico para prestadores de serviços',
                'preco_mensal': Decimal('59.90'),
                'preco_anual': Decimal('599.00'),
                'max_usuarios': 3,
                'max_produtos': 30,
                'max_pedidos_mes': 500,
                'espaco_storage_gb': 5,
                'tem_relatorios_avancados': False,
                'tem_api_acesso': False,
                'tem_suporte_prioritario': False,
                'tem_dominio_customizado': False,
                'tem_whatsapp_integration': False,
                'is_active': True,
                'ordem': 1
            }
        ]
        
        created_count = 0
        for plano_data in planos:
            tipo_slug = plano_data.pop('tipo_slug')
            tipo_loja = tipos.get(tipo_slug)
            
            if tipo_loja:
                plano, created = PlanoAssinatura.objects.get_or_create(
                    slug=plano_data['slug'],
                    defaults=plano_data
                )
                if created:
                    # Adicionar tipo de app ao ManyToMany
                    plano.tipos_loja.add(tipo_loja)
                    created_count += 1
                    self.stdout.write(f'  ✅ Plano criado: {plano.nome}')
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ {created_count} planos criados'))
        else:
            self.stdout.write('ℹ️  Planos já existem')
