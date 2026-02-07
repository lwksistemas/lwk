#!/usr/bin/env python
"""
Script para corrigir data_vencimento da loja Salao Luizao
Atualiza LojaAssinatura e FinanceiroLoja
"""
import os
import sys
import django
from datetime import date
from calendar import monthrange

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import LojaAssinatura

def corrigir_data_salao_luizao():
    """Corrige data_vencimento para próximo mês"""
    
    try:
        # Buscar loja
        loja = Loja.objects.get(slug='salao-luizao-5889')
        financeiro = loja.financeiro
        
        print(f"\n📊 Loja: {loja.nome}")
        print(f"   Slug: {loja.slug}")
        print(f"   Dia Vencimento: {financeiro.dia_vencimento}")
        print(f"\n❌ DADOS ATUAIS:")
        print(f"   FinanceiroLoja.data_proxima_cobranca: {financeiro.data_proxima_cobranca}")
        
        # Buscar LojaAssinatura
        try:
            loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
            print(f"   LojaAssinatura.data_vencimento: {loja_assinatura.data_vencimento}")
        except LojaAssinatura.DoesNotExist:
            print(f"   LojaAssinatura: NÃO ENCONTRADA")
            loja_assinatura = None
        
        # Calcular próxima data de cobrança
        hoje = date.today()
        dia_vencimento = financeiro.dia_vencimento
        
        # Calcular próximo mês
        if hoje.month == 12:
            proximo_mes = 1
            proximo_ano = hoje.year + 1
        else:
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year
        
        # Ajustar dia se o mês não tiver esse dia
        ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
        dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
        
        # Nova data
        nova_data = date(proximo_ano, proximo_mes, dia_cobranca)
        
        print(f"\n✅ NOVA DATA CALCULADA: {nova_data}")
        print(f"   Cálculo: dia {dia_vencimento} do mês {proximo_mes}/{proximo_ano}")
        
        # Confirmar atualização
        resposta = input("\n❓ Deseja atualizar? (s/n): ")
        
        if resposta.lower() == 's':
            # Atualizar FinanceiroLoja
            financeiro.data_proxima_cobranca = nova_data
            financeiro.save()
            print(f"\n✅ FinanceiroLoja.data_proxima_cobranca atualizada: {financeiro.data_proxima_cobranca}")
            
            # Atualizar LojaAssinatura
            if loja_assinatura:
                loja_assinatura.data_vencimento = nova_data
                loja_assinatura.save()
                print(f"✅ LojaAssinatura.data_vencimento atualizada: {loja_assinatura.data_vencimento}")
            
            print("\n🎉 Correção concluída com sucesso!")
            print(f"\nVerifique em:")
            print(f"   Modal: https://lwksistemas.com.br/loja/{loja.slug}/dashboard")
            print(f"   SuperAdmin: https://lwksistemas.com.br/superadmin/financeiro")
        else:
            print("\n❌ Atualização cancelada")
            
    except Loja.DoesNotExist:
        print("\n❌ Loja não encontrada!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    corrigir_data_salao_luizao()
