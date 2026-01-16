#!/usr/bin/env python3
"""
Script para criar novos tipos de loja:
1. Clínica de Estética
2. CRM Vendas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import TipoLoja, PlanoAssinatura

def criar_tipos_loja():
    """Criar os novos tipos de loja"""
    
    # 1. Clínica de Estética
    clinica, created = TipoLoja.objects.get_or_create(
        slug='clinica-estetica',
        defaults={
            'nome': 'Clínica de Estética',
            'descricao': 'Clínica de estética e beleza com agendamento online e controle de procedimentos',
            'dashboard_template': 'clinica',
            'cor_primaria': '#EC4899',  # Rosa
            'cor_secundaria': '#DB2777',
            'tem_produtos': True,  # Produtos de beleza
            'tem_servicos': True,  # Procedimentos estéticos
            'tem_agendamento': True,  # Agendamento de consultas
            'tem_delivery': False,
            'tem_estoque': True,  # Controle de produtos
        }
    )
    
    if created:
        print("✅ Tipo 'Clínica de Estética' criado com sucesso!")
    else:
        print("ℹ️ Tipo 'Clínica de Estética' já existe")
    
    # 2. CRM Vendas
    crm, created = TipoLoja.objects.get_or_create(
        slug='crm-vendas',
        defaults={
            'nome': 'CRM Vendas',
            'descricao': 'Sistema de CRM para gestão de vendas, leads e relacionamento com clientes',
            'dashboard_template': 'crm',
            'cor_primaria': '#8B5CF6',  # Roxo
            'cor_secundaria': '#7C3AED',
            'tem_produtos': False,  # Não vende produtos físicos
            'tem_servicos': True,   # Serviços de vendas
            'tem_agendamento': True,  # Agendamento de reuniões
            'tem_delivery': False,
            'tem_estoque': False,   # Não tem estoque físico
        }
    )
    
    if created:
        print("✅ Tipo 'CRM Vendas' criado com sucesso!")
    else:
        print("ℹ️ Tipo 'CRM Vendas' já existe")
    
    return clinica, crm

def criar_planos_clinica(clinica):
    """Criar planos específicos para clínica de estética"""
    
    planos_clinica = [
        {
            'nome': 'Estética Básica',
            'slug': 'estetica-basica',
            'descricao': 'Ideal para clínicas pequenas com poucos procedimentos',
            'preco_mensal': 89.90,
            'preco_anual': 899.00,
            'max_produtos': 50,
            'max_usuarios': 3,
            'max_pedidos_mes': 200,
            'espaco_storage_gb': 5,
            'tem_relatorios_avancados': False,
            'tem_api_acesso': False,
            'tem_suporte_prioritario': False,
            'tem_dominio_customizado': False,
            'tem_whatsapp_integration': True,
            'ordem': 1,
        },
        {
            'nome': 'Estética Profissional',
            'slug': 'estetica-profissional',
            'descricao': 'Para clínicas em crescimento com múltiplos profissionais',
            'preco_mensal': 149.90,
            'preco_anual': 1499.00,
            'max_produtos': 200,
            'max_usuarios': 8,
            'max_pedidos_mes': 500,
            'espaco_storage_gb': 15,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': True,
            'tem_suporte_prioritario': False,
            'tem_dominio_customizado': True,
            'tem_whatsapp_integration': True,
            'ordem': 2,
        },
        {
            'nome': 'Estética Premium',
            'slug': 'estetica-premium',
            'descricao': 'Solução completa para grandes clínicas e franquias',
            'preco_mensal': 249.90,
            'preco_anual': 2499.00,
            'max_produtos': 999999,
            'max_usuarios': 20,
            'max_pedidos_mes': 999999,
            'espaco_storage_gb': 50,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': True,
            'tem_suporte_prioritario': True,
            'tem_dominio_customizado': True,
            'tem_whatsapp_integration': True,
            'ordem': 3,
        }
    ]
    
    for plano_data in planos_clinica:
        plano, created = PlanoAssinatura.objects.get_or_create(
            slug=plano_data['slug'],
            defaults=plano_data
        )
        
        if created:
            print(f"✅ Plano '{plano.nome}' criado!")
        else:
            print(f"ℹ️ Plano '{plano.nome}' já existe")
        
        # Vincular ao tipo clínica
        plano.tipos_loja.add(clinica)

def criar_planos_crm(crm):
    """Criar planos específicos para CRM de vendas"""
    
    planos_crm = [
        {
            'nome': 'CRM Starter',
            'slug': 'crm-starter',
            'descricao': 'Ideal para pequenas equipes de vendas',
            'preco_mensal': 79.90,
            'preco_anual': 799.00,
            'max_produtos': 0,  # CRM não tem produtos
            'max_usuarios': 5,
            'max_pedidos_mes': 1000,  # Leads/oportunidades
            'espaco_storage_gb': 3,
            'tem_relatorios_avancados': False,
            'tem_api_acesso': False,
            'tem_suporte_prioritario': False,
            'tem_dominio_customizado': False,
            'tem_whatsapp_integration': True,
            'ordem': 1,
        },
        {
            'nome': 'CRM Business',
            'slug': 'crm-business',
            'descricao': 'Para equipes de vendas em crescimento',
            'preco_mensal': 129.90,
            'preco_anual': 1299.00,
            'max_produtos': 0,
            'max_usuarios': 15,
            'max_pedidos_mes': 5000,
            'espaco_storage_gb': 10,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': True,
            'tem_suporte_prioritario': False,
            'tem_dominio_customizado': True,
            'tem_whatsapp_integration': True,
            'ordem': 2,
        },
        {
            'nome': 'CRM Enterprise',
            'slug': 'crm-enterprise',
            'descricao': 'Solução completa para grandes equipes de vendas',
            'preco_mensal': 199.90,
            'preco_anual': 1999.00,
            'max_produtos': 0,
            'max_usuarios': 50,
            'max_pedidos_mes': 999999,
            'espaco_storage_gb': 25,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': True,
            'tem_suporte_prioritario': True,
            'tem_dominio_customizado': True,
            'tem_whatsapp_integration': True,
            'ordem': 3,
        }
    ]
    
    for plano_data in planos_crm:
        plano, created = PlanoAssinatura.objects.get_or_create(
            slug=plano_data['slug'],
            defaults=plano_data
        )
        
        if created:
            print(f"✅ Plano '{plano.nome}' criado!")
        else:
            print(f"ℹ️ Plano '{plano.nome}' já existe")
        
        # Vincular ao tipo CRM
        plano.tipos_loja.add(crm)

def main():
    print("🚀 Criando novos tipos de loja e planos...")
    print()
    
    # Criar tipos
    clinica, crm = criar_tipos_loja()
    print()
    
    # Criar planos para clínica
    print("📋 Criando planos para Clínica de Estética...")
    criar_planos_clinica(clinica)
    print()
    
    # Criar planos para CRM
    print("📋 Criando planos para CRM Vendas...")
    criar_planos_crm(crm)
    print()
    
    print("✅ Todos os tipos e planos foram criados com sucesso!")
    print()
    print("📊 Resumo:")
    print(f"- Total de tipos de loja: {TipoLoja.objects.count()}")
    print(f"- Total de planos: {PlanoAssinatura.objects.count()}")
    print()
    print("🎯 Próximos passos:")
    print("1. Acesse http://localhost:3000/superadmin/tipos-loja")
    print("2. Veja os novos tipos: Clínica de Estética e CRM Vendas")
    print("3. Crie lojas usando os novos tipos e planos")

if __name__ == '__main__':
    main()