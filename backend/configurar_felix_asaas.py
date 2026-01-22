#!/usr/bin/env python3
"""
Script para configurar Asaas da loja felix
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/app' if os.path.exists('/app') else '/home/luiz/Documents/lwksistemas/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production' if os.path.exists('/app') else 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.asaas_service import LojaAsaasService

def configurar_felix():
    """Configura Asaas para a loja felix"""
    print("🏪 Configurando Asaas para loja felix")
    print("=" * 40)
    
    try:
        # Buscar loja felix
        loja = Loja.objects.get(slug='felix')
        financeiro = loja.financeiro
        
        print(f"✅ Loja encontrada: {loja.nome}")
        print(f"   Owner: {loja.owner.username}")
        print(f"   CPF/CNPJ: {loja.cpf_cnpj}")
        print(f"   Plano: {loja.plano.nome}")
        print(f"   Valor mensal: R$ {financeiro.valor_mensalidade}")
        
        # Verificar se já tem dados do Asaas
        if financeiro.asaas_customer_id and financeiro.asaas_payment_id:
            print(f"\n✅ Já possui integração Asaas:")
            print(f"   Customer ID: {financeiro.asaas_customer_id}")
            print(f"   Payment ID: {financeiro.asaas_payment_id}")
            print(f"   Boleto URL: {financeiro.boleto_url[:50]}..." if financeiro.boleto_url else "   Boleto URL: Não disponível")
            print(f"   PIX disponível: {'Sim' if financeiro.pix_copy_paste else 'Não'}")
            return True
        
        print(f"\n⚠️ Sem integração Asaas - criando cobrança...")
        
        # Verificar CPF/CNPJ
        if not loja.cpf_cnpj:
            print("❌ Loja sem CPF/CNPJ - não é possível criar cobrança")
            return False
        
        # Criar cobrança no Asaas
        service = LojaAsaasService()
        resultado = service.criar_cobranca_loja(loja, financeiro)
        
        if resultado.get('success'):
            print(f"\n✅ Cobrança Asaas criada com sucesso!")
            
            # Recarregar dados
            financeiro.refresh_from_db()
            
            print(f"   Customer ID: {financeiro.asaas_customer_id}")
            print(f"   Payment ID: {financeiro.asaas_payment_id}")
            print(f"   Boleto URL: {financeiro.boleto_url[:50]}..." if financeiro.boleto_url else "   Boleto URL: Não disponível")
            print(f"   PIX disponível: {'Sim' if financeiro.pix_copy_paste else 'Não'}")
            
            return True
        else:
            print(f"\n❌ Erro ao criar cobrança Asaas:")
            print(f"   {resultado.get('error', 'Erro desconhecido')}")
            return False
            
    except Loja.DoesNotExist:
        print("❌ Loja 'felix' não encontrada!")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Configuração Asaas - Loja Felix")
    print("=" * 50)
    
    sucesso = configurar_felix()
    
    if sucesso:
        print(f"\n🎯 Resultado:")
        print("✅ Loja felix configurada com Asaas")
        print("✅ Modal de configurações funcionará corretamente")
        print(f"\n🔗 Teste em: https://lwksistemas.com.br/loja/felix/dashboard")
        print("   Login: felipe / g$uR1t@!")
    else:
        print(f"\n❌ Falha na configuração")
        print("   Verifique os logs acima para mais detalhes")

if __name__ == "__main__":
    main()