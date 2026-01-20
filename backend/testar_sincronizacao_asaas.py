#!/usr/bin/env python3
"""
Script para testar o sistema de sincronização Asaas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from superadmin.sync_service import AsaasSyncService
from superadmin.models import Loja, FinanceiroLoja, PagamentoLoja

def testar_sincronizacao():
    print("=== Testando Sistema de Sincronização Asaas ===")
    
    # Inicializar serviço
    sync_service = AsaasSyncService()
    
    if not sync_service.asaas_service.available:
        print("❌ Serviço Asaas não disponível")
        return
    
    print("✅ Serviço de sincronização inicializado")
    
    # Obter estatísticas
    print("\n=== Estatísticas Atuais ===")
    stats = sync_service.get_sync_stats()
    
    if 'error' in stats:
        print(f"❌ Erro ao obter estatísticas: {stats['error']}")
        return
    
    print(f"📊 Total de lojas: {stats['total_lojas']}")
    print(f"🔗 Lojas com Asaas: {stats['lojas_com_asaas']}")
    print(f"🔒 Lojas bloqueadas: {stats['lojas_bloqueadas']}")
    print(f"⏳ Pagamentos pendentes: {stats['pagamentos_pendentes']}")
    print(f"✅ Pagamentos pagos hoje: {stats['pagamentos_pagos_hoje']}")
    
    # Listar lojas com integração Asaas
    print("\n=== Lojas com Integração Asaas ===")
    lojas_com_asaas = Loja.objects.filter(
        is_active=True,
        financeiro__asaas_payment_id__isnull=False
    ).exclude(financeiro__asaas_payment_id='')
    
    for loja in lojas_com_asaas:
        financeiro = loja.financeiro
        status_icon = "🔒" if loja.is_blocked else "✅"
        
        print(f"{status_icon} {loja.nome}")
        print(f"   Customer ID: {financeiro.asaas_customer_id}")
        print(f"   Payment ID: {financeiro.asaas_payment_id}")
        print(f"   Status: {financeiro.status_pagamento}")
        print(f"   Dias em atraso: {loja.days_overdue}")
        
        if loja.is_blocked:
            print(f"   🔒 Bloqueada em: {loja.blocked_at}")
            print(f"   📝 Motivo: {loja.blocked_reason}")
        
        if financeiro.last_sync_at:
            print(f"   🔄 Última sync: {financeiro.last_sync_at}")
        
        if financeiro.sync_error:
            print(f"   ❌ Erro de sync: {financeiro.sync_error}")
        
        print()
    
    # Testar sincronização de uma loja específica
    if lojas_com_asaas.exists():
        loja_teste = lojas_com_asaas.first()
        print(f"=== Testando Sincronização da Loja: {loja_teste.nome} ===")
        
        resultado = sync_service.sync_loja_payments(loja_teste)
        
        if resultado['success']:
            print(f"✅ Sincronização bem-sucedida")
            print(f"📊 Pagamentos atualizados: {resultado['pagamentos_atualizados']}")
            print(f"📈 Status atual: {resultado['status']}")
            
            if resultado.get('blocked'):
                print("🔒 Loja foi BLOQUEADA por inadimplência")
            
            if resultado.get('unblocked'):
                print("🔓 Loja foi DESBLOQUEADA após pagamento")
        else:
            print(f"❌ Erro na sincronização: {resultado.get('error')}")
    
    # Mostrar pagamentos pendentes
    print("\n=== Pagamentos Pendentes ===")
    pagamentos_pendentes = PagamentoLoja.objects.filter(
        status__in=['pendente', 'atrasado']
    ).order_by('data_vencimento')
    
    for pagamento in pagamentos_pendentes[:5]:  # Mostrar apenas os 5 primeiros
        status_icon = "⏰" if pagamento.status == 'pendente' else "⚠️"
        print(f"{status_icon} {pagamento.loja.nome} - R$ {pagamento.valor}")
        print(f"   Vencimento: {pagamento.data_vencimento}")
        print(f"   Status: {pagamento.status}")
        print(f"   Asaas ID: {pagamento.asaas_payment_id}")
        print()
    
    print("=== Teste Concluído ===")

if __name__ == '__main__':
    testar_sincronizacao()