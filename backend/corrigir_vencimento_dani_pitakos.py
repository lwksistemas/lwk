"""
Script para corrigir a data de vencimento do cliente Dani Pitakos
que pagou plano anual em 09/04/2026 mas está mostrando próximo vencimento errado
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import LojaAssinatura

def corrigir_vencimento_dani():
    """Corrige a data de vencimento do cliente Dani Pitakos"""
    
    print("=" * 80)
    print("CORREÇÃO DE VENCIMENTO - DANI PITAKOS")
    print("=" * 80)
    
    # Buscar a loja pelo email do admin
    email_admin = "dani.rfoliveira@gmail.com"
    
    try:
        # Buscar loja pelo email do owner
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(email=email_admin)
        loja = Loja.objects.get(owner=user, is_active=True)
        
        print(f"\n✅ Loja encontrada:")
        print(f"   Nome: {loja.nome}")
        print(f"   Slug: {loja.slug}")
        print(f"   Tipo Assinatura: {loja.tipo_assinatura}")
        print(f"   Plano: {loja.plano.nome}")
        
        # Buscar financeiro
        financeiro = loja.financeiro
        
        print(f"\n📊 Dados Financeiros ANTES da correção:")
        print(f"   Status: {financeiro.status_pagamento}")
        print(f"   Último Pagamento: {financeiro.ultimo_pagamento}")
        print(f"   Próxima Cobrança: {financeiro.data_proxima_cobranca}")
        print(f"   Dia Vencimento: {financeiro.dia_vencimento}")
        
        # Buscar assinatura Asaas
        try:
            loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
            print(f"\n📋 Assinatura Asaas ANTES da correção:")
            print(f"   Data Vencimento: {loja_assinatura.data_vencimento}")
        except LojaAssinatura.DoesNotExist:
            loja_assinatura = None
            print(f"\n⚠️  Assinatura Asaas não encontrada")
        
        # Calcular data correta
        # Cliente pagou em 09/04/2026, plano anual deve vencer em 09/04/2027
        data_pagamento = date(2026, 4, 9)
        
        if loja.tipo_assinatura == 'anual':
            # Adicionar 365 dias (1 ano)
            proxima_data_correta = data_pagamento + timedelta(days=365)
        else:
            # Adicionar 30 dias (1 mês)
            proxima_data_correta = data_pagamento + timedelta(days=30)
        
        print(f"\n🔧 CORREÇÃO:")
        print(f"   Data do Pagamento: {data_pagamento}")
        print(f"   Tipo de Assinatura: {loja.tipo_assinatura}")
        print(f"   Próxima Data CORRETA: {proxima_data_correta}")
        
        # Confirmar antes de aplicar
        resposta = input("\n⚠️  Deseja aplicar a correção? (s/n): ")
        
        if resposta.lower() == 's':
            # Atualizar financeiro
            financeiro.data_proxima_cobranca = proxima_data_correta
            financeiro.save()
            print(f"\n✅ FinanceiroLoja atualizado")
            
            # Atualizar assinatura Asaas
            if loja_assinatura:
                loja_assinatura.data_vencimento = proxima_data_correta
                loja_assinatura.save()
                print(f"✅ LojaAssinatura atualizada")
            
            print(f"\n📊 Dados Financeiros DEPOIS da correção:")
            financeiro.refresh_from_db()
            print(f"   Próxima Cobrança: {financeiro.data_proxima_cobranca}")
            
            if loja_assinatura:
                loja_assinatura.refresh_from_db()
                print(f"\n📋 Assinatura Asaas DEPOIS da correção:")
                print(f"   Data Vencimento: {loja_assinatura.data_vencimento}")
            
            print(f"\n✅ CORREÇÃO APLICADA COM SUCESSO!")
        else:
            print(f"\n❌ Correção cancelada pelo usuário")
        
    except User.DoesNotExist:
        print(f"\n❌ Usuário com email {email_admin} não encontrado")
    except Loja.DoesNotExist:
        print(f"\n❌ Loja não encontrada para o usuário {email_admin}")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'=' * 80}\n")

if __name__ == '__main__':
    corrigir_vencimento_dani()
