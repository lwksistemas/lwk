#!/usr/bin/env python3
"""
Script para corrigir lojas que não têm integração Asaas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from superadmin.models import Loja, FinanceiroLoja
from superadmin.asaas_service import LojaAsaasService

def corrigir_lojas_sem_asaas():
    print("=== Corrigindo Lojas sem Integração Asaas ===")
    
    # Buscar lojas sem integração Asaas
    lojas_sem_asaas = []
    
    for loja in Loja.objects.filter(is_active=True):
        try:
            financeiro = loja.financeiro
            if not financeiro.asaas_customer_id or not financeiro.asaas_payment_id:
                lojas_sem_asaas.append(loja)
        except FinanceiroLoja.DoesNotExist:
            print(f"⚠️ Loja {loja.nome} não tem financeiro!")
            continue
    
    print(f"📊 Encontradas {len(lojas_sem_asaas)} lojas sem integração Asaas")
    
    if not lojas_sem_asaas:
        print("✅ Todas as lojas já têm integração Asaas!")
        return
    
    # Listar lojas
    for i, loja in enumerate(lojas_sem_asaas, 1):
        print(f"{i}. {loja.nome} (slug: {loja.slug}) - CPF/CNPJ: {loja.cpf_cnpj}")
    
    # Processar cada loja
    service = LojaAsaasService()
    
    if not service.available:
        print("❌ Serviço Asaas não disponível")
        return
    
    sucessos = 0
    erros = 0
    
    for loja in lojas_sem_asaas:
        print(f"\n=== Processando {loja.nome} ===")
        
        try:
            financeiro = loja.financeiro
            
            # Verificar se CPF/CNPJ é válido (básico)
            if not loja.cpf_cnpj or len(loja.cpf_cnpj.replace('.', '').replace('-', '').replace('/', '')) < 11:
                print(f"⚠️ CPF/CNPJ inválido: {loja.cpf_cnpj}")
                print("   Pulando esta loja...")
                erros += 1
                continue
            
            # Criar cobrança
            resultado = service.criar_cobranca_loja(loja, financeiro)
            
            if resultado.get('success'):
                print(f"✅ Cobrança criada com sucesso!")
                print(f"   Customer ID: {resultado.get('customer_id')}")
                print(f"   Payment ID: {resultado.get('payment_id')}")
                print(f"   Valor: R$ {resultado.get('value')}")
                sucessos += 1
            else:
                print(f"❌ Erro: {resultado.get('error')}")
                erros += 1
                
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            erros += 1
    
    print(f"\n=== Resumo ===")
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Erros: {erros}")
    print(f"📊 Total processado: {len(lojas_sem_asaas)}")

if __name__ == '__main__':
    corrigir_lojas_sem_asaas()