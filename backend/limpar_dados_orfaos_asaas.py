#!/usr/bin/env python
"""
Script para limpar dados órfãos do Asaas após exclusão de lojas
Remove pagamentos e clientes que não têm mais lojas associadas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from asaas_integration.models import AsaasPayment, AsaasCustomer, LojaAssinatura
from superadmin.models import Loja
from asaas_integration.deletion_service import AsaasDeletionService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def identificar_dados_orfaos():
    """Identificar dados órfãos no sistema"""
    print("🔍 Identificando dados órfãos...")
    
    # 1. Pagamentos órfãos
    pagamentos_orfaos = []
    for payment in AsaasPayment.objects.all():
        # Verificar se a loja ainda existe pela external_reference
        if payment.external_reference:
            if 'loja_' in payment.external_reference:
                loja_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
                try:
                    Loja.objects.get(slug=loja_slug, is_active=True)
                except Loja.DoesNotExist:
                    pagamentos_orfaos.append(payment)
        else:
            # Pagamento sem referência - provavelmente órfão
            pagamentos_orfaos.append(payment)
    
    # 2. Clientes órfãos
    clientes_orfaos = []
    for customer in AsaasCustomer.objects.all():
        # Verificar se tem pagamentos associados a lojas existentes
        tem_loja_ativa = False
        for payment in customer.payments.all():
            if payment.external_reference and 'loja_' in payment.external_reference:
                loja_slug = payment.external_reference.replace('loja_', '').replace('_assinatura', '').replace('_pix', '')
                try:
                    Loja.objects.get(slug=loja_slug, is_active=True)
                    tem_loja_ativa = True
                    break
                except Loja.DoesNotExist:
                    continue
        
        if not tem_loja_ativa:
            clientes_orfaos.append(customer)
    
    # 3. Assinaturas órfãs
    assinaturas_orfas = []
    for assinatura in LojaAssinatura.objects.all():
        try:
            Loja.objects.get(slug=assinatura.loja_slug, is_active=True)
        except Loja.DoesNotExist:
            assinaturas_orfas.append(assinatura)
    
    print(f"📊 Dados órfãos encontrados:")
    print(f"   - Pagamentos: {len(pagamentos_orfaos)}")
    print(f"   - Clientes: {len(clientes_orfaos)}")
    print(f"   - Assinaturas: {len(assinaturas_orfas)}")
    
    return pagamentos_orfaos, clientes_orfaos, assinaturas_orfas

def listar_pagamentos_orfaos(pagamentos_orfaos):
    """Listar detalhes dos pagamentos órfãos"""
    print("\n💰 Detalhes dos pagamentos órfãos:")
    print("-" * 80)
    
    total_valor = 0
    for payment in pagamentos_orfaos:
        print(f"ID: {payment.asaas_id}")
        print(f"Cliente: {payment.customer.name if payment.customer else 'N/A'}")
        print(f"Valor: R$ {payment.value}")
        print(f"Status: {payment.status}")
        print(f"Vencimento: {payment.due_date}")
        print(f"Referência: {payment.external_reference}")
        print(f"Criado em: {payment.created_at}")
        print("-" * 40)
        
        total_valor += float(payment.value)
    
    print(f"💸 Total em pagamentos órfãos: R$ {total_valor:.2f}")
    return total_valor

def cancelar_pagamentos_orfaos_asaas(pagamentos_orfaos):
    """Cancelar pagamentos órfãos na API do Asaas"""
    print("\n🗑️ Cancelando pagamentos órfãos na API do Asaas...")
    
    deletion_service = AsaasDeletionService()
    
    if not deletion_service.available:
        print("⚠️ Serviço Asaas não disponível - apenas limpeza local")
        return 0
    
    cancelados = 0
    for payment in pagamentos_orfaos:
        try:
            # Só tentar cancelar se estiver pendente
            if payment.status in ['PENDING', 'AWAITING_PAYMENT', 'OVERDUE']:
                deletion_service.client.delete_payment(payment.asaas_id)
                print(f"✅ Pagamento cancelado na API: {payment.asaas_id}")
                cancelados += 1
            else:
                print(f"ℹ️ Pagamento {payment.asaas_id} não cancelado (status: {payment.status})")
        except Exception as e:
            if "não pode ser removida" in str(e) or "invalid_action" in str(e):
                print(f"ℹ️ Pagamento {payment.asaas_id} não pode ser cancelado (já processado)")
            else:
                print(f"⚠️ Erro ao cancelar {payment.asaas_id}: {e}")
    
    return cancelados

def excluir_clientes_orfaos_asaas(clientes_orfaos):
    """Excluir clientes órfãos na API do Asaas"""
    print("\n🗑️ Excluindo clientes órfãos na API do Asaas...")
    
    deletion_service = AsaasDeletionService()
    
    if not deletion_service.available:
        print("⚠️ Serviço Asaas não disponível - apenas limpeza local")
        return 0
    
    excluidos = 0
    for customer in clientes_orfaos:
        try:
            deletion_service.client.delete_customer(customer.asaas_id)
            print(f"✅ Cliente excluído na API: {customer.asaas_id}")
            excluidos += 1
        except Exception as e:
            print(f"⚠️ Erro ao excluir cliente {customer.asaas_id}: {e}")
    
    return excluidos

def limpar_dados_locais(pagamentos_orfaos, clientes_orfaos, assinaturas_orfas):
    """Limpar dados órfãos do banco local"""
    print("\n🧹 Limpando dados órfãos do banco local...")
    
    # 1. Remover assinaturas órfãs
    assinaturas_removidas = 0
    for assinatura in assinaturas_orfas:
        assinatura.delete()
        assinaturas_removidas += 1
        print(f"✅ Assinatura removida: {assinatura.loja_slug}")
    
    # 2. Remover pagamentos órfãos
    pagamentos_removidos = 0
    for payment in pagamentos_orfaos:
        payment.delete()
        pagamentos_removidos += 1
        print(f"✅ Pagamento removido: {payment.asaas_id}")
    
    # 3. Remover clientes órfãos
    clientes_removidos = 0
    for customer in clientes_orfaos:
        customer.delete()
        clientes_removidos += 1
        print(f"✅ Cliente removido: {customer.asaas_id}")
    
    return {
        'assinaturas_removidas': assinaturas_removidas,
        'pagamentos_removidos': pagamentos_removidos,
        'clientes_removidos': clientes_removidos
    }

def verificar_limpeza():
    """Verificar se a limpeza foi bem-sucedida"""
    print("\n🔍 Verificando resultado da limpeza...")
    
    pagamentos_restantes = AsaasPayment.objects.count()
    clientes_restantes = AsaasCustomer.objects.count()
    assinaturas_restantes = LojaAssinatura.objects.count()
    
    print(f"📊 Dados restantes:")
    print(f"   - Pagamentos: {pagamentos_restantes}")
    print(f"   - Clientes: {clientes_restantes}")
    print(f"   - Assinaturas: {assinaturas_restantes}")
    
    if pagamentos_restantes == 0 and clientes_restantes == 0 and assinaturas_restantes == 0:
        print("✅ Limpeza completa! Todos os dados órfãos foram removidos.")
        return True
    else:
        print("⚠️ Ainda existem dados no sistema. Verificar se são legítimos.")
        return False

def main():
    """Função principal"""
    print("🧹 Iniciando limpeza de dados órfãos do Asaas...")
    print("=" * 60)
    
    try:
        # 1. Identificar dados órfãos
        pagamentos_orfaos, clientes_orfaos, assinaturas_orfas = identificar_dados_orfaos()
        
        if not pagamentos_orfaos and not clientes_orfaos and not assinaturas_orfas:
            print("✅ Nenhum dado órfão encontrado! Sistema já está limpo.")
            return
        
        # 2. Listar detalhes dos pagamentos órfãos
        total_valor = listar_pagamentos_orfaos(pagamentos_orfaos)
        
        # 3. Confirmar limpeza
        print(f"\n⚠️ ATENÇÃO: Serão removidos {len(pagamentos_orfaos)} pagamentos totalizando R$ {total_valor:.2f}")
        print("Esta operação é IRREVERSÍVEL!")
        
        confirmacao = input("\nDeseja continuar? (digite 'SIM' para confirmar): ")
        
        if confirmacao.upper() != 'SIM':
            print("❌ Operação cancelada pelo usuário.")
            return
        
        # 4. Cancelar pagamentos na API do Asaas
        pagamentos_cancelados = cancelar_pagamentos_orfaos_asaas(pagamentos_orfaos)
        
        # 5. Excluir clientes na API do Asaas
        clientes_excluidos = excluir_clientes_orfaos_asaas(clientes_orfaos)
        
        # 6. Limpar dados locais
        resultado_local = limpar_dados_locais(pagamentos_orfaos, clientes_orfaos, assinaturas_orfas)
        
        # 7. Verificar resultado
        limpeza_completa = verificar_limpeza()
        
        # 8. Resumo final
        print("\n" + "=" * 60)
        print("RESUMO DA LIMPEZA")
        print("=" * 60)
        print(f"💰 Valor total removido: R$ {total_valor:.2f}")
        print(f"🗑️ Pagamentos cancelados na API: {pagamentos_cancelados}")
        print(f"👥 Clientes excluídos na API: {clientes_excluidos}")
        print(f"📋 Assinaturas removidas: {resultado_local['assinaturas_removidas']}")
        print(f"💳 Pagamentos removidos localmente: {resultado_local['pagamentos_removidos']}")
        print(f"👤 Clientes removidos localmente: {resultado_local['clientes_removidos']}")
        
        if limpeza_completa:
            print("\n🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("✅ Sistema financeiro está limpo e pronto para uso.")
        else:
            print("\n⚠️ LIMPEZA PARCIAL")
            print("Alguns dados ainda existem - verificar se são legítimos.")
        
    except Exception as e:
        print(f"❌ Erro durante a limpeza: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()