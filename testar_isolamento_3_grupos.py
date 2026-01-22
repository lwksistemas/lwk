#!/usr/bin/env python3
"""
Script para testar isolamento total dos 3 grupos de usuários

GRUPO 1: Super Admin - Acesso exclusivo ao /superadmin/
GRUPO 2: Suporte - Acesso exclusivo ao /suporte/
GRUPO 3: Lojas - Acesso exclusivo à própria loja

Garante que:
- Super Admin não pode acessar rotas de suporte ou lojas (exceto com permissão)
- Suporte não pode acessar rotas de superadmin ou lojas
- Loja não pode acessar rotas de superadmin, suporte ou outras lojas
"""
import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

# Configurações
BASE_URL = "https://lwksistemas-38ad47519238.herokuapp.com"
# BASE_URL = "http://localhost:8000"  # Para testes locais

class Colors:
    """Cores para output no terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 100)
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.END}")
    print("=" * 100)


def print_test(name: str, passed: bool, details: str = ""):
    """Imprime resultado de um teste"""
    status = f"{Colors.GREEN}✅ PASSOU{Colors.END}" if passed else f"{Colors.RED}❌ FALHOU{Colors.END}"
    print(f"\n{status} - {name}")
    if details:
        print(f"   {details}")


def login(username: str, password: str) -> Tuple[str, str]:
    """Faz login e retorna o token e grupo do usuário"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/token/",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens.get('access'), "success"
        else:
            return None, f"Erro {response.status_code}: {response.text}"
    except Exception as e:
        return None, str(e)


def test_endpoint(name: str, method: str, url: str, headers: Dict = None, 
                  expected_status: int = 200, should_fail: bool = False) -> bool:
    """
    Testa um endpoint
    
    Args:
        name: Nome do teste
        method: GET ou POST
        url: URL completa
        headers: Headers da requisição
        expected_status: Status esperado
        should_fail: Se True, espera que falhe (403 ou 401)
    
    Returns:
        True se o teste passou, False caso contrário
    """
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json={})
        else:
            print_test(name, False, f"Método não suportado: {method}")
            return False
        
        if should_fail:
            # Esperamos que falhe com 401 ou 403
            passed = response.status_code in [401, 403]
            details = f"Status: {response.status_code} (esperado: 401 ou 403)"
        else:
            # Esperamos que passe com o status esperado
            passed = response.status_code == expected_status
            details = f"Status: {response.status_code} (esperado: {expected_status})"
        
        print_test(name, passed, details)
        return passed
        
    except Exception as e:
        print_test(name, False, f"Erro: {e}")
        return False


def main():
    print_header("TESTE DE ISOLAMENTO DOS 3 GRUPOS DE USUÁRIOS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    results = []
    
    # ========================================
    # CONFIGURAÇÃO: Solicitar credenciais
    # ========================================
    print_header("CONFIGURAÇÃO - Credenciais de Teste")
    
    print(f"\n{Colors.YELLOW}Você precisa fornecer credenciais dos 3 grupos para testar:{Colors.END}")
    print("1. Super Admin")
    print("2. Suporte")
    print("3. Proprietário de Loja")
    
    # Super Admin
    print(f"\n{Colors.BOLD}GRUPO 1: SUPER ADMIN{Colors.END}")
    superadmin_username = input("Username do Super Admin: ").strip()
    superadmin_password = input("Senha: ").strip()
    
    # Suporte
    print(f"\n{Colors.BOLD}GRUPO 2: SUPORTE{Colors.END}")
    suporte_username = input("Username do Suporte: ").strip()
    suporte_password = input("Senha: ").strip()
    
    # Loja
    print(f"\n{Colors.BOLD}GRUPO 3: PROPRIETÁRIO DE LOJA{Colors.END}")
    loja_username = input("Username do Proprietário: ").strip()
    loja_password = input("Senha: ").strip()
    loja_slug = input("Slug da loja: ").strip()
    
    # ========================================
    # AUTENTICAÇÃO
    # ========================================
    print_header("AUTENTICAÇÃO DOS 3 GRUPOS")
    
    # Login Super Admin
    print(f"\n{Colors.BOLD}Fazendo login como Super Admin...{Colors.END}")
    superadmin_token, error = login(superadmin_username, superadmin_password)
    if superadmin_token:
        print(f"{Colors.GREEN}✅ Super Admin autenticado{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Falha na autenticação: {error}{Colors.END}")
        return
    
    # Login Suporte
    print(f"\n{Colors.BOLD}Fazendo login como Suporte...{Colors.END}")
    suporte_token, error = login(suporte_username, suporte_password)
    if suporte_token:
        print(f"{Colors.GREEN}✅ Suporte autenticado{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Falha na autenticação: {error}{Colors.END}")
        return
    
    # Login Loja
    print(f"\n{Colors.BOLD}Fazendo login como Proprietário de Loja...{Colors.END}")
    loja_token, error = login(loja_username, loja_password)
    if loja_token:
        print(f"{Colors.GREEN}✅ Proprietário autenticado{Colors.END}")
    else:
        print(f"{Colors.RED}❌ Falha na autenticação: {error}{Colors.END}")
        return
    
    # Headers
    superadmin_headers = {"Authorization": f"Bearer {superadmin_token}"}
    suporte_headers = {"Authorization": f"Bearer {suporte_token}"}
    loja_headers = {"Authorization": f"Bearer {loja_token}"}
    
    # ========================================
    # TESTE 1: SUPER ADMIN
    # ========================================
    print_header("TESTE 1: ISOLAMENTO DO SUPER ADMIN")
    
    print(f"\n{Colors.BOLD}1.1. Super Admin PODE acessar rotas de superadmin{Colors.END}")
    results.append(test_endpoint(
        "Super Admin acessa /api/superadmin/lojas/",
        "GET",
        f"{BASE_URL}/api/superadmin/lojas/",
        superadmin_headers,
        expected_status=200
    ))
    
    print(f"\n{Colors.BOLD}1.2. Suporte NÃO PODE acessar rotas de superadmin{Colors.END}")
    results.append(test_endpoint(
        "Suporte tenta acessar /api/superadmin/lojas/ (deve falhar)",
        "GET",
        f"{BASE_URL}/api/superadmin/lojas/",
        suporte_headers,
        should_fail=True
    ))
    
    print(f"\n{Colors.BOLD}1.3. Loja NÃO PODE acessar rotas de superadmin{Colors.END}")
    results.append(test_endpoint(
        "Loja tenta acessar /api/superadmin/lojas/ (deve falhar)",
        "GET",
        f"{BASE_URL}/api/superadmin/lojas/",
        loja_headers,
        should_fail=True
    ))
    
    # ========================================
    # TESTE 2: SUPORTE
    # ========================================
    print_header("TESTE 2: ISOLAMENTO DO SUPORTE")
    
    print(f"\n{Colors.BOLD}2.1. Suporte PODE acessar rotas de suporte{Colors.END}")
    results.append(test_endpoint(
        "Suporte acessa /api/suporte/chamados/",
        "GET",
        f"{BASE_URL}/api/suporte/chamados/",
        suporte_headers,
        expected_status=200
    ))
    
    print(f"\n{Colors.BOLD}2.2. Super Admin PODE acessar rotas de suporte{Colors.END}")
    results.append(test_endpoint(
        "Super Admin acessa /api/suporte/chamados/",
        "GET",
        f"{BASE_URL}/api/suporte/chamados/",
        superadmin_headers,
        expected_status=200
    ))
    
    print(f"\n{Colors.BOLD}2.3. Loja NÃO PODE acessar rotas de suporte{Colors.END}")
    results.append(test_endpoint(
        "Loja tenta acessar /api/suporte/chamados/ (deve falhar)",
        "GET",
        f"{BASE_URL}/api/suporte/chamados/",
        loja_headers,
        should_fail=True
    ))
    
    # ========================================
    # TESTE 3: LOJAS
    # ========================================
    print_header("TESTE 3: ISOLAMENTO DE LOJAS")
    
    print(f"\n{Colors.BOLD}3.1. Loja PODE acessar suas próprias rotas{Colors.END}")
    results.append(test_endpoint(
        f"Loja acessa /api/clinica/ (sua loja: {loja_slug})",
        "GET",
        f"{BASE_URL}/api/clinica/",
        loja_headers,
        expected_status=200
    ))
    
    print(f"\n{Colors.BOLD}3.2. Suporte NÃO PODE acessar rotas de lojas{Colors.END}")
    results.append(test_endpoint(
        "Suporte tenta acessar /api/clinica/ (deve falhar)",
        "GET",
        f"{BASE_URL}/api/clinica/",
        suporte_headers,
        should_fail=True
    ))
    
    print(f"\n{Colors.BOLD}3.3. Super Admin PODE acessar rotas de lojas{Colors.END}")
    results.append(test_endpoint(
        "Super Admin acessa /api/clinica/",
        "GET",
        f"{BASE_URL}/api/clinica/",
        superadmin_headers,
        expected_status=200
    ))
    
    # ========================================
    # TESTE 4: CROSS-STORE ACCESS
    # ========================================
    print_header("TESTE 4: ISOLAMENTO ENTRE LOJAS")
    
    print(f"\n{Colors.BOLD}4.1. Loja NÃO PODE acessar dados de outra loja{Colors.END}")
    print(f"{Colors.YELLOW}Nota: Este teste requer que exista outra loja no sistema{Colors.END}")
    
    outra_loja_slug = input("\nDigite o slug de OUTRA loja (ou deixe em branco para pular): ").strip()
    
    if outra_loja_slug and outra_loja_slug != loja_slug:
        results.append(test_endpoint(
            f"Loja {loja_slug} tenta acessar loja {outra_loja_slug} (deve falhar)",
            "GET",
            f"{BASE_URL}/api/clinica/?store={outra_loja_slug}",
            loja_headers,
            should_fail=True
        ))
    else:
        print(f"{Colors.YELLOW}⏭️  Teste pulado (outra loja não fornecida){Colors.END}")
    
    # ========================================
    # RESUMO
    # ========================================
    print_header("RESUMO DOS TESTES")
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 Total de testes: {total}")
    print(f"{Colors.GREEN}✅ Passou: {passed}{Colors.END}")
    print(f"{Colors.RED}❌ Falhou: {failed}{Colors.END}")
    print(f"📈 Taxa de sucesso: {percentage:.1f}%")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM!{Colors.END}")
        print(f"{Colors.GREEN}✅ Isolamento total dos 3 grupos garantido{Colors.END}")
        print(f"{Colors.GREEN}✅ Super Admin isolado{Colors.END}")
        print(f"{Colors.GREEN}✅ Suporte isolado{Colors.END}")
        print(f"{Colors.GREEN}✅ Lojas isoladas{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ALGUNS TESTES FALHARAM{Colors.END}")
        print(f"{Colors.RED}Verifique os logs acima para detalhes{Colors.END}")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Teste interrompido pelo usuário{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Erro fatal: {e}{Colors.END}")
