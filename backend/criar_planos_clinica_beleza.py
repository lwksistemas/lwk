"""
Script para criar Planos de Assinatura para Clínica da Beleza
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import TipoLoja, PlanoAssinatura
from decimal import Decimal

def criar_planos_clinica_beleza():
    print("💎 Criando Planos de Assinatura para Clínica da Beleza...")
    
    # Buscar o tipo de loja Clínica da Beleza
    try:
        tipo_clinica = TipoLoja.objects.get(slug='clinica-da-beleza')
        print(f"✅ Tipo de loja encontrado: {tipo_clinica.nome}")
    except TipoLoja.DoesNotExist:
        print("❌ Tipo de loja 'Clínica da Beleza' não encontrado!")
        print("Execute primeiro: python criar_tipo_loja_clinica_beleza.py")
        return
    
    # Limpar planos existentes para este tipo de loja (opcional)
    planos_existentes = PlanoAssinatura.objects.filter(tipos_loja=tipo_clinica)
    if planos_existentes.exists():
        print(f"⚠️  Encontrados {planos_existentes.count()} planos existentes para Clínica da Beleza")
        resposta = input("Deseja removê-los e criar novos? (s/n): ")
        if resposta.lower() == 's':
            for plano in planos_existentes:
                plano.tipos_loja.remove(tipo_clinica)
                if not plano.tipos_loja.exists():
                    plano.delete()
            print("✅ Planos antigos removidos")
    
    # ============================================================================
    # PLANO 1: BÁSICO
    # ============================================================================
    plano_basico, created = PlanoAssinatura.objects.get_or_create(
        slug='clinica-beleza-basico',
        defaults={
            'nome': 'Básico',
            'descricao': 'Ideal para clínicas iniciantes com até 50 pacientes ativos',
            'preco_mensal': Decimal('79.90'),
            'preco_anual': Decimal('799.00'),  # 2 meses grátis
            'max_produtos': 50,  # Pacientes
            'max_usuarios': 2,   # Profissionais
            'max_pedidos_mes': 100,  # Agendamentos
            'espaco_storage_gb': 2,
            'tem_relatorios_avancados': False,
            'tem_api_acesso': False,
            'tem_suporte_prioritario': False,
            'tem_dominio_customizado': False,
            'tem_whatsapp_integration': False,
            'is_active': True,
            'ordem': 1,
        }
    )
    plano_basico.tipos_loja.add(tipo_clinica)
    print(f"{'✅ Criado' if created else '✅ Atualizado'}: {plano_basico.nome} - R$ {plano_basico.preco_mensal}/mês")
    
    # ============================================================================
    # PLANO 2: PROFISSIONAL (MAIS POPULAR)
    # ============================================================================
    plano_profissional, created = PlanoAssinatura.objects.get_or_create(
        slug='clinica-beleza-profissional',
        defaults={
            'nome': 'Profissional',
            'descricao': 'Perfeito para clínicas em crescimento com até 200 pacientes ativos',
            'preco_mensal': Decimal('149.90'),
            'preco_anual': Decimal('1499.00'),  # 2 meses grátis
            'max_produtos': 200,  # Pacientes
            'max_usuarios': 5,    # Profissionais
            'max_pedidos_mes': 500,  # Agendamentos
            'espaco_storage_gb': 10,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': False,
            'tem_suporte_prioritario': True,
            'tem_dominio_customizado': False,
            'tem_whatsapp_integration': True,
            'is_active': True,
            'ordem': 2,
        }
    )
    plano_profissional.tipos_loja.add(tipo_clinica)
    print(f"{'✅ Criado' if created else '✅ Atualizado'}: {plano_profissional.nome} - R$ {plano_profissional.preco_mensal}/mês ⭐ MAIS POPULAR")
    
    # ============================================================================
    # PLANO 3: PREMIUM
    # ============================================================================
    plano_premium, created = PlanoAssinatura.objects.get_or_create(
        slug='clinica-beleza-premium',
        defaults={
            'nome': 'Premium',
            'descricao': 'Para clínicas estabelecidas com pacientes ilimitados e recursos avançados',
            'preco_mensal': Decimal('299.90'),
            'preco_anual': Decimal('2999.00'),  # 2 meses grátis
            'max_produtos': 999999,  # Ilimitado
            'max_usuarios': 20,      # Profissionais
            'max_pedidos_mes': 999999,  # Ilimitado
            'espaco_storage_gb': 50,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': True,
            'tem_suporte_prioritario': True,
            'tem_dominio_customizado': True,
            'tem_whatsapp_integration': True,
            'is_active': True,
            'ordem': 3,
        }
    )
    plano_premium.tipos_loja.add(tipo_clinica)
    print(f"{'✅ Criado' if created else '✅ Atualizado'}: {plano_premium.nome} - R$ {plano_premium.preco_mensal}/mês")
    
    # ============================================================================
    # PLANO 4: ENTERPRISE (OPCIONAL)
    # ============================================================================
    plano_enterprise, created = PlanoAssinatura.objects.get_or_create(
        slug='clinica-beleza-enterprise',
        defaults={
            'nome': 'Enterprise',
            'descricao': 'Solução completa para redes de clínicas com múltiplas unidades',
            'preco_mensal': Decimal('599.90'),
            'preco_anual': Decimal('5999.00'),  # 2 meses grátis
            'max_produtos': 999999,  # Ilimitado
            'max_usuarios': 999999,  # Ilimitado
            'max_pedidos_mes': 999999,  # Ilimitado
            'espaco_storage_gb': 200,
            'tem_relatorios_avancados': True,
            'tem_api_acesso': True,
            'tem_suporte_prioritario': True,
            'tem_dominio_customizado': True,
            'tem_whatsapp_integration': True,
            'is_active': True,
            'ordem': 4,
        }
    )
    plano_enterprise.tipos_loja.add(tipo_clinica)
    print(f"{'✅ Criado' if created else '✅ Atualizado'}: {plano_enterprise.nome} - R$ {plano_enterprise.preco_mensal}/mês")
    
    print("\n" + "="*80)
    print("📊 RESUMO DOS PLANOS CRIADOS")
    print("="*80)
    
    planos = PlanoAssinatura.objects.filter(tipos_loja=tipo_clinica).order_by('ordem')
    for plano in planos:
        print(f"\n💎 {plano.nome.upper()}")
        print(f"   Preço: R$ {plano.preco_mensal}/mês ou R$ {plano.preco_anual}/ano")
        print(f"   Pacientes: {'Ilimitados' if plano.max_produtos > 999000 else plano.max_produtos}")
        print(f"   Profissionais: {'Ilimitados' if plano.max_usuarios > 999000 else plano.max_usuarios}")
        print(f"   Agendamentos/mês: {'Ilimitados' if plano.max_pedidos_mes > 999000 else plano.max_pedidos_mes}")
        print(f"   Storage: {plano.espaco_storage_gb} GB")
        print(f"   Recursos:")
        if plano.tem_relatorios_avancados:
            print(f"      ✅ Relatórios Avançados")
        if plano.tem_whatsapp_integration:
            print(f"      ✅ Integração WhatsApp")
        if plano.tem_suporte_prioritario:
            print(f"      ✅ Suporte Prioritário")
        if plano.tem_dominio_customizado:
            print(f"      ✅ Domínio Customizado")
        if plano.tem_api_acesso:
            print(f"      ✅ Acesso à API")
    
    print("\n" + "="*80)
    print("✨ Planos criados com sucesso!")
    print("="*80)
    print("\n📝 Próximos passos:")
    print("   1. Acesse o Superadmin")
    print("   2. Crie uma nova loja do tipo 'Clínica da Beleza'")
    print("   3. Escolha um dos planos criados")
    print("   4. Teste o dashboard em: /loja/[slug]/dashboard")

if __name__ == '__main__':
    criar_planos_clinica_beleza()
