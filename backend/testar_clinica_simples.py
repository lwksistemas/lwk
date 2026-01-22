#!/usr/bin/env python3
"""
Script simples para testar a clínica de estética
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clinica_estetica.models import Cliente, Profissional, Procedimento
from clinica_estetica.serializers import ClienteSerializer

def test_model_creation():
    """Testa criação de modelos"""
    print("🧪 Testando criação de modelos da clínica")
    
    try:
        # Criar cliente
        cliente = Cliente.objects.create(
            nome="João Silva Teste",
            email="joao@teste.com",
            telefone="(11) 99999-9999",
            cpf="123.456.789-00",
            endereco="Rua Teste, 123",
            cidade="São Paulo",
            estado="SP"
        )
        print(f"✅ Cliente criado: {cliente.nome} (ID: {cliente.id})")
        
        # Testar serializer
        serializer = ClienteSerializer(cliente)
        print(f"✅ Serializer funcionando: {len(serializer.data)} campos")
        
        # Testar validação com dados vazios
        empty_data = {
            'nome': '',
            'email': '',
            'telefone': '',
            'data_nascimento': ''
        }
        
        serializer_empty = ClienteSerializer(data=empty_data)
        if serializer_empty.is_valid():
            print("❌ Serializer aceitou dados vazios (problema!)")
        else:
            print(f"✅ Serializer rejeitou dados vazios: {serializer_empty.errors}")
        
        # Testar com dados válidos
        valid_data = {
            'nome': 'Maria Santos',
            'email': 'maria@teste.com',
            'telefone': '(11) 88888-8888',
            'data_nascimento': '1985-05-15'
        }
        
        serializer_valid = ClienteSerializer(data=valid_data)
        if serializer_valid.is_valid():
            print("✅ Serializer aceitou dados válidos")
            cliente_novo = serializer_valid.save()
            print(f"✅ Cliente salvo via serializer: {cliente_novo.nome}")
        else:
            print(f"❌ Serializer rejeitou dados válidos: {serializer_valid.errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def check_database():
    """Verifica o banco de dados"""
    print("\n📊 Verificando banco de dados")
    
    try:
        clientes = Cliente.objects.all()
        print(f"Total de clientes: {clientes.count()}")
        
        for cliente in clientes[:3]:
            print(f"  - {cliente.nome} ({cliente.email}) - {cliente.created_at}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

def test_field_validation():
    """Testa validação de campos específicos"""
    print("\n🔍 Testando validação de campos")
    
    # Teste com data_nascimento vazia
    test_cases = [
        {
            'nome': 'Teste 1',
            'email': 'teste1@email.com',
            'telefone': '(11) 11111-1111',
            'data_nascimento': '',  # Campo vazio
        },
        {
            'nome': 'Teste 2',
            'email': 'teste2@email.com',
            'telefone': '(11) 22222-2222',
            'data_nascimento': None,  # Campo null
        },
        {
            'nome': 'Teste 3',
            'email': 'teste3@email.com',
            'telefone': '(11) 33333-3333',
            # data_nascimento ausente
        }
    ]
    
    for i, data in enumerate(test_cases, 1):
        print(f"\n  Teste {i}: {data}")
        serializer = ClienteSerializer(data=data)
        
        if serializer.is_valid():
            try:
                cliente = serializer.save()
                print(f"    ✅ Sucesso: Cliente {cliente.nome} criado")
            except Exception as e:
                print(f"    ❌ Erro ao salvar: {e}")
        else:
            print(f"    ❌ Validação falhou: {serializer.errors}")

if __name__ == "__main__":
    print("🚀 Teste simples da clínica de estética")
    print("=" * 50)
    
    check_database()
    success = test_model_creation()
    test_field_validation()
    
    print("\n" + "=" * 50)
    print(f"Resultado: {'✅ Sucesso' if success else '❌ Falhou'}")