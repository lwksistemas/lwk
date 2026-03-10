from django.core.management.base import BaseCommand
from superadmin.models import TipoLoja, PlanoAssinatura


class Command(BaseCommand):
    help = 'Cria tipos de app e planos iniciais (Clínica Estética, CRM Vendas, Clínica da Beleza)'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Criando tipos de app e planos...\n')
        
        # ============================================
        # 1. CLÍNICA DE ESTÉTICA
        # ============================================
        clinica_estetica, created = TipoLoja.objects.get_or_create(
            codigo='CLIEST',
            defaults={
                'nome': 'Clínica de Estética',
                'slug': 'clinica-estetica',
                'descricao': 'Sistema completo para clínicas de estética com agendamentos, prontuários e controle financeiro',
                'cor_primaria': '#10B981',
                'cor_secundaria': '#059669',
                'tem_agendamento': True,
                'tem_servicos': True,
                'tem_produtos': False
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Tipo de App criado: Clínica de Estética'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Tipo de App já existe: Clínica de Estética'))
        
        # Plano para Clínica de Estética
        plano_clinica, created = PlanoAssinatura.objects.get_or_create(
            nome='Plano Clínica Estética',
            defaults={
                'slug': 'plano-clinica-estetica',
                'descricao': 'Plano completo para clínicas de estética',
                'preco_mensal': 99.90,
                'preco_anual': 999.00,
                'max_usuarios': 10,
                'max_pedidos_mes': 1000,
                'espaco_storage_gb': 5,
                'tem_suporte_prioritario': True,
                'tem_relatorios_avancados': True,
                'is_active': True
            }
        )
        if created:
            plano_clinica.tipos_loja.add(clinica_estetica)
            self.stdout.write(self.style.SUCCESS('  ✅ Plano criado e vinculado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️ Plano já existe'))
        
        # ============================================
        # 2. CRM VENDAS
        # ============================================
        crm_vendas, created = TipoLoja.objects.get_or_create(
            codigo='CRMVND',
            defaults={
                'nome': 'CRM Vendas',
                'slug': 'crm-vendas',
                'descricao': 'Sistema de CRM para gestão de vendas, leads, oportunidades e pipeline comercial',
                'cor_primaria': '#3B82F6',
                'cor_secundaria': '#2563EB',
                'tem_agendamento': True,
                'tem_servicos': False,
                'tem_produtos': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Tipo de App criado: CRM Vendas'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Tipo de App já existe: CRM Vendas'))
        
        # Plano para CRM Vendas
        plano_crm, created = PlanoAssinatura.objects.get_or_create(
            nome='Plano CRM Vendas',
            defaults={
                'slug': 'plano-crm-vendas',
                'descricao': 'Plano completo para gestão de vendas e pipeline comercial',
                'preco_mensal': 149.90,
                'preco_anual': 1499.00,
                'max_usuarios': 20,
                'max_pedidos_mes': 2000,
                'espaco_storage_gb': 10,
                'tem_suporte_prioritario': True,
                'tem_relatorios_avancados': True,
                'tem_api_acesso': True,
                'is_active': True
            }
        )
        if created:
            plano_crm.tipos_loja.add(crm_vendas)
            self.stdout.write(self.style.SUCCESS('  ✅ Plano criado e vinculado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️ Plano já existe'))
        
        # ============================================
        # 3. CLÍNICA DA BELEZA
        # ============================================
        clinica_beleza, created = TipoLoja.objects.get_or_create(
            codigo='CLIBEL',
            defaults={
                'nome': 'Clínica da Beleza',
                'slug': 'clinica-beleza',
                'descricao': 'Sistema para clínicas de beleza com agendamentos, profissionais e controle de serviços',
                'cor_primaria': '#EC4899',
                'cor_secundaria': '#DB2777',
                'tem_agendamento': True,
                'tem_servicos': True,
                'tem_produtos': False
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Tipo de App criado: Clínica da Beleza'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Tipo de App já existe: Clínica da Beleza'))
        
        # Plano para Clínica da Beleza
        plano_beleza, created = PlanoAssinatura.objects.get_or_create(
            nome='Plano Clínica Beleza',
            defaults={
                'slug': 'plano-clinica-beleza',
                'descricao': 'Plano completo para clínicas de beleza e estética',
                'preco_mensal': 89.90,
                'preco_anual': 899.00,
                'max_usuarios': 15,
                'max_pedidos_mes': 1500,
                'espaco_storage_gb': 5,
                'tem_suporte_prioritario': True,
                'tem_relatorios_avancados': True,
                'is_active': True
            }
        )
        if created:
            plano_beleza.tipos_loja.add(clinica_beleza)
            self.stdout.write(self.style.SUCCESS('  ✅ Plano criado e vinculado'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️ Plano já existe'))
        
        # ============================================
        # RESUMO
        # ============================================
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ Tipos de App e Planos criados com sucesso!\n'))
        
        self.stdout.write('📋 Resumo:')
        self.stdout.write(f'  1. Clínica de Estética (ID: {clinica_estetica.id}) - R$ 99,90/mês')
        self.stdout.write(f'  2. CRM Vendas (ID: {crm_vendas.id}) - R$ 149,90/mês')
        self.stdout.write(f'  3. Clínica da Beleza (ID: {clinica_beleza.id}) - R$ 89,90/mês')
        self.stdout.write('='*60)
