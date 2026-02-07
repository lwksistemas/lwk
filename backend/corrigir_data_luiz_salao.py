#!/usr/bin/env python
"""
Script para corrigir data de próxima cobrança da loja Luiz Salao
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from datetime import date

loja_slug = 'luiz-salao-5889'

try:
    loja = Loja.objects.get(slug=loja_slug)
    financeiro = loja.financeiro
    
    print(f"\n{'='*60}")
    print(f"Corrigindo data de próxima cobrança - {loja.nome}")
    print(f"{'='*60}\n")
    
    print(f"📊 Dados Atuais:")
    print(f"   - Data Próxima Cobrança: {financeiro.data_proxima_cobranca}")
    print(f"   - Dia Vencimento: {financeiro.dia_vencimento}")
    
    # Corrigir para 10/04/2026
    nova_data = date(2026, 4, 10)
    
    print(f"\n🔧 Corrigindo para: {nova_data}")
    
    financeiro.data_proxima_cobranca = nova_data
    financeiro.save()
    
    print(f"✅ Data corrigida com sucesso!")
    
    # Verificar
    financeiro.refresh_from_db()
    print(f"\n📊 Dados Após Correção:")
    print(f"   - Data Próxima Cobrança: {financeiro.data_proxima_cobranca}")
    
    print(f"\n{'='*60}\n")
    
except Loja.DoesNotExist:
    print(f"❌ Loja {loja_slug} não encontrada")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
