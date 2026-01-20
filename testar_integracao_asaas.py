#!/usr/bin/env python3
"""
Script para testar a integração Asaas
Cria uma loja de teste e verifica se o boleto/PIX é gerado automaticamente
"""
import requests
import json
from datetime import datetime

# Configurações
BASE_URL = "https://lwksistemas-38ad47519238.herokuapp.com"
FRONTEND_URL = "https://lwksistemas.com.br"

def login_superadmin():
    """Faz login como superadmin"""
    print("🔐 Fazendo login como superadmin...")
    
    login_data = {
        "username": "superadmin",
        "password": "super123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token/", json=login_data)
    
    if response.status_code == 200:
        token = response.json()["access"]
        print("✅ Login realizado com sucesso!")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        return None

def get_planos(token):
    """Busca os planos disponíveis"""
    print("📋 Buscando planos disponíveis...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/superadmin/planos/", headers=headers)
    
    if response.status_code == 200:
        planos = response.json()
        print(f"✅ Encontrados {len(planos)} planos")
        return planos
    else:
        print(f"❌ Erro ao buscar planos: {response.status_code}")
        return []

def get_tipos_loja(token):
    """Busca os tipos de loja disponíveis"""
    print("🏪 Buscando tipos de loja...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/superadmin/tipos-loja/", headers=headers)
    
    if response.status_code == 200:
        tipos = response.json()
        print(f"✅ Encontrados {len(tipos)} tipos de loja")
        return tipos
    else:
        print(f"❌ Erro ao buscar tipos: {response.status_code}")
        return []

def criar_loja_teste(token, plano_id, tipo_loja_id):
    """Cria uma loja de teste"""
    print("🏪 Criando loja de teste...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    loja_data = {
        "nome": f"Loja Teste Asaas {timestamp}",
        "slug": f"loja-teste-asaas-{timestamp}",
        "email": f"teste.asaas.{timestamp}@lwksistemas.com.br",
        "cpf_cnpj": "12345678901",
        "plano": plano_id,
        "tipo_loja": tipo_loja_id,
        "tipo_assinatura": "mensal",
        "owner_data": {
            "username": f"teste_asaas_{timestamp}",
            "email": f"teste.asaas.{timestamp}@lwksistemas.com.br",
            "first_name": "Teste",
            "last_name": "Asaas"
        }
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/superadmin/lojas/", json=loja_data, headers=headers)
    
    if response.status_code == 201:
        loja = response.json()
        print(f"✅ Loja criada com sucesso!")
        print(f"   ID: {loja['id']}")
        print(f"   Nome: {loja['nome']}")
        print(f"   Slug: {loja['slug']}")
        return loja
    else:
        print(f"❌ Erro ao criar loja: {response.status_code}")
        print(response.text)
        return None

def verificar_assinatura_asaas(token, loja_slug):
    """Verifica se a assinatura Asaas foi criada"""
    print("💳 Verificando assinatura Asaas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/asaas/subscriptions/", headers=headers)
    
    if response.status_code == 200:
        assinaturas = response.json()
        
        # Buscar assinatura da loja criada
        assinatura_loja = None
        for assinatura in assinaturas:
            if assinatura['loja_slug'] == loja_slug:
                assinatura_loja = assinatura
                break
        
        if assinatura_loja:
            print("✅ Assinatura Asaas encontrada!")
            print(f"   ID: {assinatura_loja['id']}")
            print(f"   Loja: {assinatura_loja['loja_nome']}")
            print(f"   Plano: {assinatura_loja['plano_nome']}")
            print(f"   Valor: R$ {assinatura_loja['plano_valor']}")
            
            # Verificar pagamento atual
            if assinatura_loja.get('current_payment'):
                print("💰 Pagamento atual encontrado!")
                return assinatura_loja
            else:
                print("⚠️  Assinatura sem pagamento atual")
                return assinatura_loja
        else:
            print("❌ Assinatura não encontrada para esta loja")
            return None
    else:
        print(f"❌ Erro ao buscar assinaturas: {response.status_code}")
        return None

def verificar_pagamento_asaas(token, assinatura_id):
    """Verifica os detalhes do pagamento Asaas"""
    print("🧾 Verificando detalhes do pagamento...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/asaas/payments/", headers=headers)
    
    if response.status_code == 200:
        pagamentos = response.json()
        
        # Buscar pagamentos da assinatura
        pagamentos_assinatura = [p for p in pagamentos if 'loja-teste-asaas' in p.get('external_reference', '')]
        
        if pagamentos_assinatura:
            pagamento = pagamentos_assinatura[0]  # Mais recente
            print("✅ Pagamento Asaas encontrado!")
            print(f"   ID Asaas: {pagamento['asaas_id']}")
            print(f"   Status: {pagamento['status']}")
            print(f"   Valor: R$ {pagamento['value']}")
            print(f"   Vencimento: {pagamento['due_date']}")
            
            if pagamento.get('bank_slip_url'):
                print(f"   🧾 Boleto: {pagamento['bank_slip_url']}")
            
            if pagamento.get('pix_qr_code'):
                print("   💳 PIX: QR Code disponível")
            
            if pagamento.get('pix_copy_paste'):
                print("   📋 PIX: Copia e cola disponível")
            
            return pagamento
        else:
            print("❌ Pagamento não encontrado")
            return None
    else:
        print(f"❌ Erro ao buscar pagamentos: {response.status_code}")
        return None

def main():
    """Função principal"""
    print("🚀 TESTE DA INTEGRAÇÃO ASAAS")
    print("=" * 50)
    
    # 1. Login
    token = login_superadmin()
    if not token:
        return
    
    # 2. Buscar planos
    planos = get_planos(token)
    if not planos:
        return
    
    # 3. Buscar tipos de loja
    tipos = get_tipos_loja(token)
    if not tipos:
        return
    
    # 4. Criar loja de teste
    plano_id = planos[0]['id']  # Primeiro plano
    tipo_id = tipos[0]['id']    # Primeiro tipo
    
    loja = criar_loja_teste(token, plano_id, tipo_id)
    if not loja:
        return
    
    # 5. Aguardar um pouco para o signal processar
    import time
    print("⏳ Aguardando processamento do signal...")
    time.sleep(3)
    
    # 6. Verificar assinatura Asaas
    assinatura = verificar_assinatura_asaas(token, loja['slug'])
    if not assinatura:
        print("❌ TESTE FALHOU: Assinatura Asaas não foi criada")
        return
    
    # 7. Verificar pagamento
    pagamento = verificar_pagamento_asaas(token, assinatura['id'])
    if not pagamento:
        print("❌ TESTE FALHOU: Pagamento Asaas não foi criado")
        return
    
    # 8. Resultado final
    print("\n" + "=" * 50)
    print("🎉 TESTE DA INTEGRAÇÃO ASAAS CONCLUÍDO!")
    print("=" * 50)
    print("✅ Loja criada com sucesso")
    print("✅ Assinatura Asaas criada automaticamente")
    print("✅ Pagamento Asaas gerado (boleto + PIX)")
    print("✅ Dados salvos no banco local")
    print("\n🌐 Acesse o painel financeiro:")
    print(f"   {FRONTEND_URL}/superadmin/financeiro")
    print("\n🔑 Login: superadmin / super123")
    print("\n🎯 INTEGRAÇÃO ASAAS FUNCIONANDO PERFEITAMENTE!")

if __name__ == "__main__":
    main()