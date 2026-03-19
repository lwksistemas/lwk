#!/usr/bin/env python
"""Verifica se as tabelas do CRM foram criadas para a loja 132"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from crm_vendas.models import Lead, Oportunidade, Proposta, Contrato, AssinaturaDigital, ProdutoServico
from tenants.middleware import set_current_loja_id

# Configurar loja 132
set_current_loja_id(132)

print("=" * 60)
print("VERIFICAÇÃO DA LOJA 132")
print("=" * 60)

try:
    print("\n✅ Verificando tabelas do CRM...")
    
    leads = Lead.objects.count()
    print(f"  • Leads: {leads}")
    
    oportunidades = Oportunidade.objects.count()
    print(f"  • Oportunidades: {oportunidades}")
    
    propostas = Proposta.objects.count()
    print(f"  • Propostas: {propostas}")
    
    contratos = Contrato.objects.count()
    print(f"  • Contratos: {contratos}")
    
    assinaturas = AssinaturaDigital.objects.count()
    print(f"  • Assinaturas Digitais: {assinaturas}")
    
    produtos = ProdutoServico.objects.count()
    print(f"  • Produtos/Serviços: {produtos}")
    
    print("\n✅ TODAS AS TABELAS EXISTEM E ESTÃO ACESSÍVEIS!")
    print(f"📊 Total de registros: {leads + oportunidades + propostas + contratos + assinaturas + produtos}")
    
    if (leads + oportunidades + propostas + contratos + assinaturas + produtos) == 0:
        print("\n✅ LOJA ESTÁ LIMPA (SEM DADOS DE TESTE)!")
    else:
        print("\n⚠️  LOJA TEM DADOS!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
