#!/usr/bin/env python
"""
Script para atualizar data_proxima_cobranca da loja FELIX
Calcula próximo dia 10 baseado na data atual
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

def atualizar_data_proxima_cobranca():
    """Atualiza data_proxima_cobranca para próximo dia 10"""
    
    try:
        # Buscar loja FELIX
        loja = Loja.objects.get(slug='felix-r0172')
        financeiro = loja.financeiro
        
        print(f"\n📊 Loja: {loja.nome}")
        print(f"   Slug: {loja.slug}")
        print(f"   Status Pagamento: {financeiro.status_pagamento}")
        print(f"   Último Pagamento: {financeiro.ultimo_pagamento}")
        print(f"   Data Próxima Cobrança ATUAL: {financeiro.data_proxima_cobranca}")
        print(f"   Dia Vencimento: {financeiro.dia_vencimento}")
        
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
        
        print(f"\n✅ Nova Data Próxima Cobrança: {nova_data}")
        print(f"   Cálculo: dia {dia_vencimento} do mês {proximo_mes}/{proximo_ano}")
        
        # Confirmar atualização
        resposta = input("\n❓ Deseja atualizar? (s/n): ")
        
        if resposta.lower() == 's':
            financeiro.data_proxima_cobranca = nova_data
            financeiro.save()
            print("\n✅ Data atualizada com sucesso!")
            print(f"   Nova data: {financeiro.data_proxima_cobranca}")
        else:
            print("\n❌ Atualização cancelada")
            
    except Loja.DoesNotExist:
        print("\n❌ Loja não encontrada!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == '__main__':
    atualizar_data_proxima_cobranca()
