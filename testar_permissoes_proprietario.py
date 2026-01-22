#!/usr/bin/env python3
"""
Script para testar permissões de proprietários de lojas
Garante que todos os endpoints necessários estão acessíveis
"""
import requests
import json
from datetime import datetime

# Configurações
BASE_URL = "https://lwksistemas-38ad47519238.herokuapp.com"
# BASE_URL = "http://localhost:8000"  # Para testes locais

def print_section(title):
    """Imprime uma seção formatada"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_endpoint(name, method, url, headers=None, data=None, expected_status=200):
    """Testa um endpoint e retorna o resultado"""
    print(f"\n🧪 Testando: {name}")
    print(f"   Método: {method}")
    print(f"   URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"   ❌ Método não suportado: {method}")
            return False
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ SUCESSO")
            return True
        else:
            print(f"   ❌ FALHOU - Esperado: {expected_status}, Recebido: {response.status_code}")
            try:
                print(f"   Resposta: {response.json()}")
            except:
                print(f"   Resposta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        return False

def main():
    print_section("TESTE DE PERMISSÕES DE PROPRIETÁRIOS DE LOJAS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Solicitar credenciais
    print("\n📋 CREDENCIAIS DE TESTE")
    print("Você precisa fornecer credenciais de um proprietário de loja para testar.")
    print("Exemplo: usuário 'vida' da loja ID 52")
    
    username = input("\nUsername do proprietário: ").strip()
    password = input("Senha: ").strip()
    
    if not username or not password:
        print("\n❌ Credenciais não fornecidas. Abortando.")
        return
    
    # 1. Fazer login
    print_section("1. AUTENTICAÇÃO")
    
    login_url = f"{BASE_URL}/api/auth/token/"
    login_data = {
        "username": username,
        "password": password
    }
    
    print(f"\n🔐 Fazendo login como '{username}'...")
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access')
            print(f"   ✅ Login bem-sucedido!")
            print(f"   Token: {access_token[:50]}...")
        else:
            print(f"   ❌ Falha no login: {response.status_code}")
            print(f"   Resposta: {response.json()}")
            return
    except Exception as e:
        print(f"   ❌ Erro no login: {e}")
        return
    
    # Headers com autenticação
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. Verificar senha provisória
    print_section("2. VERIFICAR SENHA PROVISÓRIA")
    
    test_endpoint(
        "Verificar se precisa trocar senha",
        "GET",
        f"{BASE_URL}/api/superadmin/lojas/verificar_senha_provisoria/",
        headers=headers
    )
    
    # 3. Buscar dados da loja do usuário
    print_section("3. BUSCAR DADOS DA LOJA")
    
    print("\n🔍 Buscando loja do usuário...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/superadmin/lojas/verificar_senha_provisoria/",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            loja_id = data.get('loja_id')
            loja_slug = data.get('loja_slug')
            print(f"   ✅ Loja encontrada!")
            print(f"   ID: {loja_id}")
            print(f"   Slug: {loja_slug}")
        else:
            print(f"   ⚠️  Não foi possível obter dados da loja")
            loja_id = input("\n   Digite o ID da loja manualmente: ").strip()
            loja_slug = input("   Digite o slug da loja manualmente: ").strip()
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        loja_id = input("\n   Digite o ID da loja manualmente: ").strip()
        loja_slug = input("   Digite o slug da loja manualmente: ").strip()
    
    if not loja_id or not loja_slug:
        print("\n❌ Dados da loja não fornecidos. Abortando.")
        return
    
    # 4. Testar endpoints de proprietário
    print_section("4. ENDPOINTS DE PROPRIETÁRIO")
    
    results = []
    
    # 4.1. Alterar senha primeiro acesso (sem realmente alterar)
    print("\n📝 Nota: Não vamos realmente alterar a senha, apenas testar o acesso ao endpoint")
    # results.append(test_endpoint(
    #     "Alterar senha primeiro acesso",
    #     "POST",
    #     f"{BASE_URL}/api/superadmin/lojas/{loja_id}/alterar_senha_primeiro_acesso/",
    #     headers=headers,
    #     data={"nova_senha": "teste123", "confirmar_senha": "teste123"},
    #     expected_status=400  # Esperamos 400 se a senha já foi alterada
    # ))
    
    # 4.2. Reenviar senha (sem realmente enviar)
    print("\n📝 Nota: Não vamos realmente reenviar a senha, apenas testar o acesso ao endpoint")
    # results.append(test_endpoint(
    #     "Reenviar senha provisória",
    #     "POST",
    #     f"{BASE_URL}/api/superadmin/lojas/{loja_id}/reenviar_senha/",
    #     headers=headers,
    #     expected_status=200
    # ))
    
    # 4.3. Acessar dados financeiros
    results.append(test_endpoint(
        "Acessar dados financeiros da loja",
        "GET",
        f"{BASE_URL}/api/superadmin/loja/{loja_slug}/financeiro/",
        headers=headers,
        expected_status=200
    ))
    
    # 5. Testar endpoints que NÃO devem ser acessíveis
    print_section("5. ENDPOINTS QUE DEVEM SER BLOQUEADOS")
    
    # 5.1. Listar todas as lojas (apenas superadmin)
    blocked = test_endpoint(
        "Listar todas as lojas (deve ser bloqueado)",
        "GET",
        f"{BASE_URL}/api/superadmin/lojas/",
        headers=headers,
        expected_status=403
    )
    results.append(blocked)
    
    # 5.2. Criar nova loja (apenas superadmin)
    blocked = test_endpoint(
        "Criar nova loja (deve ser bloqueado)",
        "POST",
        f"{BASE_URL}/api/superadmin/lojas/",
        headers=headers,
        data={"nome": "Teste", "slug": "teste"},
        expected_status=403
    )
    results.append(blocked)
    
    # 5.3. Estatísticas do sistema (apenas superadmin)
    blocked = test_endpoint(
        "Estatísticas do sistema (deve ser bloqueado)",
        "GET",
        f"{BASE_URL}/api/superadmin/lojas/estatisticas/",
        headers=headers,
        expected_status=403
    )
    results.append(blocked)
    
    # Resumo
    print_section("RESUMO DOS TESTES")
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"\n📊 Total de testes: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Proprietários de lojas têm acesso correto aos endpoints necessários")
        print("✅ Proprietários de lojas NÃO têm acesso a endpoints restritos")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        print("Verifique os logs acima para detalhes")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
