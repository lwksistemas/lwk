"""
Script para corrigir números de propostas e contratos existentes.
Gera números sequenciais para propostas e contratos que não têm número ou têm números duplicados.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from crm_vendas.models import Proposta, Contrato
from django_tenants.utils import schema_context, get_tenant_model

def corrigir_numeros_propostas():
    """Corrige números de propostas por loja."""
    print("🔧 Corrigindo números de propostas...")
    
    Tenant = get_tenant_model()
    tenants = Tenant.objects.exclude(schema_name='public')
    total_corrigidas = 0
    
    for tenant in tenants:
        with schema_context(tenant.schema_name):
            print(f"\n📍 Tenant: {tenant.schema_name}")
            
            # Buscar todas as propostas ordenadas por ID (ordem de criação)
            propostas = Proposta.objects.all().order_by('id')
            
            if not propostas.exists():
                print("   ℹ️  Nenhuma proposta encontrada")
                continue
            
            # Renumerar todas as propostas sequencialmente
            for idx, proposta in enumerate(propostas, start=1):
                numero_novo = str(idx).zfill(3)  # 001, 002, 003...
                
                if proposta.numero != numero_novo:
                    numero_antigo = proposta.numero or '(vazio)'
                    proposta.numero = numero_novo
                    proposta.save(update_fields=['numero'])
                    print(f"   ✅ Proposta ID {proposta.id}: {numero_antigo} → {numero_novo}")
                    total_corrigidas += 1
                else:
                    print(f"   ✓ Proposta ID {proposta.id}: {proposta.numero} (já correto)")
    
    print(f"\n✅ Total de propostas corrigidas: {total_corrigidas}")
    return total_corrigidas

def corrigir_numeros_contratos():
    """Corrige números de contratos por loja."""
    print("\n🔧 Corrigindo números de contratos...")
    
    Tenant = get_tenant_model()
    tenants = Tenant.objects.exclude(schema_name='public')
    total_corrigidos = 0
    
    for tenant in tenants:
        with schema_context(tenant.schema_name):
            print(f"\n📍 Tenant: {tenant.schema_name}")
            
            # Buscar todos os contratos ordenados por ID (ordem de criação)
            contratos = Contrato.objects.all().order_by('id')
            
            if not contratos.exists():
                print("   ℹ️  Nenhum contrato encontrado")
                continue
            
            # Renumerar todos os contratos sequencialmente
            for idx, contrato in enumerate(contratos, start=1):
                numero_novo = str(idx).zfill(3)  # 001, 002, 003...
                
                if contrato.numero != numero_novo:
                    numero_antigo = contrato.numero or '(vazio)'
                    contrato.numero = numero_novo
                    contrato.save(update_fields=['numero'])
                    print(f"   ✅ Contrato ID {contrato.id}: {numero_antigo} → {numero_novo}")
                    total_corrigidos += 1
                else:
                    print(f"   ✓ Contrato ID {contrato.id}: {contrato.numero} (já correto)")
    
    print(f"\n✅ Total de contratos corrigidos: {total_corrigidos}")
    return total_corrigidos

if __name__ == '__main__':
    print("=" * 80)
    print("CORREÇÃO DE NÚMEROS DE PROPOSTAS E CONTRATOS")
    print("=" * 80)
    
    try:
        propostas_corrigidas = corrigir_numeros_propostas()
        contratos_corrigidos = corrigir_numeros_contratos()
        
        print("\n" + "=" * 80)
        print("✅ CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   • Propostas corrigidas: {propostas_corrigidas}")
        print(f"   • Contratos corrigidos: {contratos_corrigidos}")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
