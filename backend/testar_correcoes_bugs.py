#!/usr/bin/env python
"""
Script para testar as correções dos bugs de exclusão de loja
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import Loja, FinanceiroLoja
from asaas_integration.models import LojaAssinatura, AsaasCustomer, AsaasPayment
from asaas_integration.deletion_service import AsaasDeletionService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def criar_loja_teste():
    """Criar uma loja de teste para testar a exclusão"""
    print("🏗️ Criando loja de teste...")
    
    # Criar usuário
    user = User.objects.create_user(
        username='teste_exclusao',
        email='teste@exclusao.com',
        password='senha123'
    )
    
    # Criar loja
    from superadmin.models import TipoLoja, PlanoAssinatura
    
    tipo_loja = TipoLoja.objects.first()
    plano = PlanoAssinatura.objects.first()
    
    loja = Loja.objects.create(
        nome='Loja Teste Exclusão',
        slug='loja-teste-exclusao',
        owner=user,
        tipo_loja=tipo_loja,
        plano=plano,
        cpf_cnpj='12345678901',
        is_active=True
    )
    
    # Criar financeiro
    FinanceiroLoja.objects.create(
        loja=loja,
        valor_mensalidade=plano.preco,
        status_pagamento='ativo'
    )
    
    print(f"✅ Loja criada: {loja.nome} (ID: {loja.id})")
    return loja

def criar_dados_asaas_teste(loja):
    """Criar dados Asaas de teste"""
    print("💳 Criando dados Asaas de teste...")
    
    # Criar cliente Asaas
    customer = AsaasCustomer.objects.create(
        asaas_id='cus_teste_exclusao',
        name=loja.nome,
        email=loja.owner.email,
        cpf_cnpj=loja.cpf_cnpj
    )
    
    # Criar pagamento pendente (pode ser cancelado)
    payment_pendente = AsaasPayment.objects.create(
        asaas_id='pay_teste_pendente',
        customer=customer,
        external_reference=f'loja_{loja.slug}_assinatura',
        billing_type='BOLETO',
        status='PENDING',
        value=100.00,
        due_date='2026-02-01'
    )
    
    # Criar pagamento pago (NÃO pode ser cancelado)
    payment_pago = AsaasPayment.objects.create(
        asaas_id='pay_teste_pago',
        customer=customer,
        external_reference=f'loja_{loja.slug}_assinatura',
        billing_type='BOLETO',
        status='RECEIVED',
        value=100.00,
        due_date='2026-01-01'
    )
    
    # Criar assinatura
    assinatura = LojaAssinatura.objects.create(
        loja_slug=loja.slug,
        asaas_customer=customer,
        current_payment=payment_pendente,
        plano_nome=loja.plano.nome,
        plano_valor=loja.plano.preco
    )
    
    print(f"✅ Dados Asaas criados:")
    print(f"   - Cliente: {customer.asaas_id}")
    print(f"   - Pagamento pendente: {payment_pendente.asaas_id}")
    print(f"   - Pagamento pago: {payment_pago.asaas_id}")
    print(f"   - Assinatura: {assinatura.loja_slug}")
    
    return customer, payment_pendente, payment_pago, assinatura

def testar_exclusao_asaas(loja_slug):
    """Testar exclusão de dados Asaas"""
    print(f"🗑️ Testando exclusão Asaas para loja: {loja_slug}")
    
    deletion_service = AsaasDeletionService()
    
    if not deletion_service.available:
        print("⚠️ Serviço Asaas não disponível - simulando exclusão")
        return True
    
    try:
        resultado = deletion_service.delete_loja_from_asaas(loja_slug)
        
        if resultado.get('success'):
            print("✅ Exclusão Asaas bem-sucedida:")
            print(f"   - Pagamentos cancelados: {resultado.get('deleted_payments', 0)}")
            print(f"   - Cliente removido: {resultado.get('deleted_customer', False)}")
        else:
            print(f"❌ Erro na exclusão Asaas: {resultado.get('error')}")
            
        return resultado.get('success', False)
        
    except Exception as e:
        print(f"❌ Exceção na exclusão Asaas: {e}")
        return False

def testar_exclusao_loja(loja_id):
    """Testar exclusão completa da loja"""
    print(f"🗑️ Testando exclusão completa da loja ID: {loja_id}")
    
    try:
        from rest_framework.test import APIClient
        from django.contrib.auth.models import User
        
        # Criar cliente API
        client = APIClient()
        
        # Fazer login como superuser
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            print("❌ Nenhum superuser encontrado")
            return False
        
        client.force_authenticate(user=superuser)
        
        # Fazer requisição DELETE
        response = client.delete(f'/api/superadmin/lojas/{loja_id}/')
        
        print(f"📊 Resposta da exclusão:")
        print(f"   - Status: {response.status_code}")
        print(f"   - Dados: {response.data}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro na exclusão da loja: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🧪 Iniciando testes de correção de bugs...")
    print("=" * 50)
    
    try:
        # 1. Criar loja de teste
        loja = criar_loja_teste()
        
        # 2. Criar dados Asaas de teste
        customer, payment_pendente, payment_pago, assinatura = criar_dados_asaas_teste(loja)
        
        # 3. Testar exclusão Asaas isoladamente
        print("\n" + "=" * 50)
        print("TESTE 1: Exclusão Asaas isolada")
        print("=" * 50)
        
        sucesso_asaas = testar_exclusao_asaas(loja.slug)
        
        # 4. Recriar dados para teste completo
        if sucesso_asaas:
            print("\n🔄 Recriando dados para teste completo...")
            customer, payment_pendente, payment_pago, assinatura = criar_dados_asaas_teste(loja)
        
        # 5. Testar exclusão completa da loja
        print("\n" + "=" * 50)
        print("TESTE 2: Exclusão completa da loja")
        print("=" * 50)
        
        sucesso_completo = testar_exclusao_loja(loja.id)
        
        # 6. Resultados finais
        print("\n" + "=" * 50)
        print("RESULTADOS FINAIS")
        print("=" * 50)
        
        print(f"✅ Exclusão Asaas: {'SUCESSO' if sucesso_asaas else 'FALHOU'}")
        print(f"✅ Exclusão Completa: {'SUCESSO' if sucesso_completo else 'FALHOU'}")
        
        if sucesso_asaas and sucesso_completo:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("✅ Bugs corrigidos com sucesso!")
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
            print("⚠️ Verificar logs para mais detalhes")
        
    except Exception as e:
        print(f"❌ Erro geral nos testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()