#!/usr/bin/env python3
"""
Script para testar as APIs da clínica de estética
"""
import os
import sys
import django
import requests
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Cliente, Profissional, Procedimento

def test_api_endpoints():
    """Testa os endpoints da API da clínica"""
    base_url = "https://lwksistemas-38ad47519238.herokuapp.com/api/clinica"
    
    # Teste 1: Listar clientes
    print("🧪 Testando GET /api/clinica/clientes/")
    try:
        response = requests.get(f"{base_url}/clientes/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sucesso! {len(data)} clientes encontrados")
        else:
            print(f"❌ Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Teste 2: Criar cliente
    print("\n🧪 Testando POST /api/clinica/clientes/")
    cliente_data = {
        "nome": "Cliente Teste API",
        "email": "teste@api.com",
        "telefone": "(11) 99999-9999",
        "cpf": "123.456.789-00",
        "data_nascimento": "1990-01-01",
        "endereco": "Rua Teste, 123",
        "cidade": "São Paulo",
        "estado": "SP",
        "observacoes": "Cliente criado via teste de API"
    }
    
    try:
        response = requests.post(
            f"{base_url}/clientes/",
            json=cliente_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Cliente criado com sucesso! ID: {data.get('id')}")
            return data.get('id')
        else:
            print(f"❌ Erro: {response.text}")
            print(f"Dados enviados: {json.dumps(cliente_data, indent=2)}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    return None

def test_local_creation():
    """Testa criação local no banco de dados"""
    print("\n🧪 Testando criação local no banco de dados")
    
    try:
        cliente = Cliente.objects.create(
            nome="Cliente Teste Local",
            email="local@teste.com",
            telefone="(11) 88888-8888",
            cpf="987.654.321-00",
            endereco="Rua Local, 456",
            cidade="Rio de Janeiro",
            estado="RJ"
        )
        print(f"✅ Cliente criado localmente! ID: {cliente.id}")
        
        # Verificar se foi salvo
        cliente_salvo = Cliente.objects.get(id=cliente.id)
        print(f"✅ Cliente verificado: {cliente_salvo.nome}")
        
        return cliente.id
    except Exception as e:
        print(f"❌ Erro na criação local: {e}")
        return None

def check_database_status():
    """Verifica o status do banco de dados"""
    print("\n📊 Verificando status do banco de dados")
    
    try:
        total_clientes = Cliente.objects.count()
        total_profissionais = Profissional.objects.count()
        total_procedimentos = Procedimento.objects.count()
        
        print(f"📈 Estatísticas:")
        print(f"   - Clientes: {total_clientes}")
        print(f"   - Profissionais: {total_profissionais}")
        print(f"   - Procedimentos: {total_procedimentos}")
        
        # Listar alguns clientes
        if total_clientes > 0:
            print(f"\n👥 Últimos 5 clientes:")
            for cliente in Cliente.objects.order_by('-created_at')[:5]:
                print(f"   - {cliente.nome} ({cliente.email})")
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando testes das APIs da clínica de estética")
    print("=" * 60)
    
    # Verificar banco local
    check_database_status()
    
    # Testar criação local
    local_id = test_local_creation()
    
    # Testar APIs remotas
    remote_id = test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("📋 Resumo dos testes:")
    print(f"   - Criação local: {'✅ Sucesso' if local_id else '❌ Falhou'}")
    print(f"   - API remota: {'✅ Sucesso' if remote_id else '❌ Falhou'}")
    
    if not remote_id:
        print("\n🔍 Possíveis causas do erro 400:")
        print("   1. Validação de campos obrigatórios")
        print("   2. Formato de dados incorreto")
        print("   3. Problemas de serialização")
        print("   4. Configuração de CORS")
        print("   5. Middleware de autenticação")