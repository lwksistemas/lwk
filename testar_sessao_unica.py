#!/usr/bin/env python3
"""
Teste de Sessão Única
Valida que apenas uma sessão pode estar ativa por vez
"""
import requests
import time
from colorama import Fore, Style, init

init(autoreset=True)

# Configuração
API_URL = "https://lwksistemas-38ad47519238.herokuapp.com"
# API_URL = "http://localhost:8000"  # Para teste local

# Credenciais do Super Admin
USERNAME = "superadmin"
PASSWORD = "super123"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'='*80}\n")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ️  {text}")

def login(device_name):
    """Faz login e retorna o token"""
    print_info(f"Fazendo login no {device_name}...")
    
    response = requests.post(
        f"{API_URL}/api/auth/superadmin/login/",
        json={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        print_success(f"Login bem-sucedido no {device_name}")
        print_info(f"Token: {token[:50]}...")
        return token
    else:
        print_error(f"Falha no login no {device_name}: {response.status_code}")
        print_error(f"Resposta: {response.text}")
        return None

def test_api_call(token, device_name):
    """Testa uma chamada de API com o token"""
    print_info(f"Testando API com token do {device_name}...")
    
    response = requests.get(
        f"{API_URL}/api/superadmin/lojas/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    if response.status_code == 200:
        print_success(f"API funcionando com token do {device_name}")
        return True
    elif response.status_code == 401:
        data = response.json()
        code = data.get('code', 'UNKNOWN')
        message = data.get('message', 'Sem mensagem')
        print_error(f"Token do {device_name} foi invalidado!")
        print_error(f"Código: {code}")
        print_error(f"Mensagem: {message}")
        return False
    else:
        print_error(f"Erro na API com token do {device_name}: {response.status_code}")
        print_error(f"Resposta: {response.text}")
        return False

def main():
    print_header("🔒 TESTE DE SESSÃO ÚNICA - Sistema LWK")
    
    print(f"{Fore.WHITE}Testando que apenas UMA sessão pode estar ativa por vez")
    print(f"{Fore.WHITE}Usuário: {USERNAME}")
    print(f"{Fore.WHITE}API: {API_URL}\n")
    
    # PASSO 1: Login no Celular
    print_header("📱 PASSO 1: Login no Celular")
    token_celular = login("CELULAR")
    
    if not token_celular:
        print_error("Não foi possível fazer login no celular. Abortando teste.")
        return
    
    time.sleep(1)
    
    # PASSO 2: Testar API com token do celular
    print_header("📱 PASSO 2: Testar API com Token do Celular")
    celular_ok = test_api_call(token_celular, "CELULAR")
    
    if not celular_ok:
        print_error("Token do celular não está funcionando. Abortando teste.")
        return
    
    time.sleep(2)
    
    # PASSO 3: Login no Computador (deve invalidar sessão do celular)
    print_header("💻 PASSO 3: Login no Computador (deve invalidar celular)")
    token_computador = login("COMPUTADOR")
    
    if not token_computador:
        print_error("Não foi possível fazer login no computador. Abortando teste.")
        return
    
    time.sleep(1)
    
    # PASSO 4: Testar API com token do computador (deve funcionar)
    print_header("💻 PASSO 4: Testar API com Token do Computador")
    computador_ok = test_api_call(token_computador, "COMPUTADOR")
    
    time.sleep(1)
    
    # PASSO 5: Testar API com token do celular (DEVE FALHAR!)
    print_header("📱 PASSO 5: Testar API com Token do Celular (DEVE FALHAR)")
    celular_ainda_ok = test_api_call(token_celular, "CELULAR")
    
    # RESULTADO FINAL
    print_header("📊 RESULTADO DO TESTE")
    
    if computador_ok and not celular_ainda_ok:
        print_success("✅ TESTE PASSOU!")
        print_success("✅ Sistema está bloqueando múltiplas sessões corretamente")
        print_success("✅ Apenas uma sessão pode estar ativa por vez")
        print()
        print(f"{Fore.GREEN}{'='*80}")
        print(f"{Fore.GREEN}SISTEMA DE SESSÃO ÚNICA FUNCIONANDO PERFEITAMENTE!")
        print(f"{Fore.GREEN}{'='*80}")
    else:
        print_error("❌ TESTE FALHOU!")
        if celular_ainda_ok:
            print_error("❌ Token do celular ainda está funcionando")
            print_error("❌ Sistema NÃO está bloqueando múltiplas sessões")
        if not computador_ok:
            print_error("❌ Token do computador não está funcionando")
        print()
        print(f"{Fore.RED}{'='*80}")
        print(f"{Fore.RED}SISTEMA DE SESSÃO ÚNICA NÃO ESTÁ FUNCIONANDO!")
        print(f"{Fore.RED}{'='*80}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n{Fore.RED}Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
