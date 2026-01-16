#!/usr/bin/env python
"""
Script para configurar dados iniciais do Super Admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import TipoLoja, PlanoAssinatura, Loja, FinanceiroLoja, UsuarioSistema
from datetime import date, timedelta

print("=" * 60)
print("CONFIGURANDO SUPER ADMIN")
print("=" * 60)

# 1. Criar Tipos de Loja
print("\n📦 Criando Tipos de Loja...")
tipos = [
    {
        'nome': 'E-commerce',
        'descricao': 'Loja virtual para venda de produtos',
        'dashboard_template': 'ecommerce',
        'cor_primaria': '#10B981',
        'tem_produtos': True,
        'tem_delivery': True,
    },
    {
        'nome': 'Serviços',
        'descricao': 'Prestação de serviços com agendamento',
        'dashboard_template': 'servicos',
        'cor_primaria': '#3B82F6',
        'tem_servicos': True,
        'tem_agendamento': True,
    },
    {
        'nome': 'Restaurante',
        'descricao': 'Delivery de comida e bebidas',
        'dashboard_template': 'restaurante',
        'cor_primaria': '#EF4444',
        'tem_produtos': True,
        'tem_delivery': True,
    },
]

for tipo_data in tipos:
    tipo, created = TipoLoja.objects.get_or_create(
        slug=tipo_data['nome'].lower().replace(' ', '-'),
        defaults=tipo_data
    )
    if created:
        print(f"  ✅ {tipo.nome}")
    else:
        print(f"  ℹ️  {tipo.nome} (já existe)")

# 2. Criar Planos de Assinatura
print("\n💎 Criando Planos de Assinatura...")
planos = [
    {
        'nome': 'Básico',
        'slug': 'basico',
        'descricao': 'Ideal para começar',
        'preco_mensal': 49.90,
        'preco_anual': 499.00,
        'max_produtos': 50,
        'max_usuarios': 2,
        'max_pedidos_mes': 100,
        'espaco_storage_gb': 2,
        'ordem': 1,
    },
    {
        'nome': 'Profissional',
        'slug': 'profissional',
        'descricao': 'Para negócios em crescimento',
        'preco_mensal': 99.90,
        'preco_anual': 999.00,
        'max_produtos': 200,
        'max_usuarios': 5,
        'max_pedidos_mes': 500,
        'espaco_storage_gb': 10,
        'tem_relatorios_avancados': True,
        'tem_api_acesso': True,
        'ordem': 2,
    },
    {
        'nome': 'Enterprise',
        'slug': 'enterprise',
        'descricao': 'Solução completa para grandes empresas',
        'preco_mensal': 299.90,
        'preco_anual': 2999.00,
        'max_produtos': 999999,
        'max_usuarios': 50,
        'max_pedidos_mes': 999999,
        'espaco_storage_gb': 100,
        'tem_relatorios_avancados': True,
        'tem_api_acesso': True,
        'tem_suporte_prioritario': True,
        'tem_dominio_customizado': True,
        'tem_whatsapp_integration': True,
        'ordem': 3,
    },
]

for plano_data in planos:
    plano, created = PlanoAssinatura.objects.get_or_create(
        slug=plano_data['slug'],
        defaults=plano_data
    )
    if created:
        print(f"  ✅ {plano.nome} - R$ {plano.preco_mensal}/mês")
    else:
        print(f"  ℹ️  {plano.nome} (já existe)")

# 3. Criar Usuário de Suporte
print("\n👥 Criando Usuário de Suporte...")
if not User.objects.filter(username='suporte').exists():
    suporte_user = User.objects.create_user(
        username='suporte',
        email='suporte@sistema.com',
        password='suporte123',
        is_staff=True
    )
    UsuarioSistema.objects.create(
        user=suporte_user,
        tipo='suporte',
        pode_acessar_todas_lojas=True
    )
    print("  ✅ Usuário 'suporte' criado")
else:
    print("  ℹ️  Usuário 'suporte' já existe")

# 4. Criar Lojas de Exemplo
print("\n🏪 Criando Lojas de Exemplo...")
superadmin = User.objects.filter(is_superuser=True).first()

if superadmin:
    tipo_ecommerce = TipoLoja.objects.get(slug='e-commerce')
    plano_basico = PlanoAssinatura.objects.get(slug='basico')
    
    loja, created = Loja.objects.get_or_create(
        slug='loja-exemplo',
        defaults={
            'nome': 'Loja Exemplo',
            'descricao': 'Loja de demonstração',
            'tipo_loja': tipo_ecommerce,
            'plano': plano_basico,
            'owner': superadmin,
            'is_trial': True,
            'trial_ends_at': date.today() + timedelta(days=30),
        }
    )
    
    if created:
        # Criar financeiro
        FinanceiroLoja.objects.create(
            loja=loja,
            data_proxima_cobranca=date.today() + timedelta(days=30),
            valor_mensalidade=plano_basico.preco_mensal,
            status_pagamento='pendente'
        )
        print(f"  ✅ {loja.nome}")
        print(f"     URL Login: {loja.login_page_url}")
    else:
        print(f"  ℹ️  {loja.nome} (já existe)")

print("\n" + "=" * 60)
print("✅ CONFIGURAÇÃO CONCLUÍDA!")
print("=" * 60)
print("\n📝 Acesse o Super Admin:")
print("   URL: http://localhost:3000/superadmin/dashboard")
print("   Usuário: superadmin")
print("   Senha: super123")
print("\n" + "=" * 60)
