#!/usr/bin/env python3
"""
Teste de Cache no Heroku
Verifica se o DatabaseCache está funcionando corretamente
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache
from colorama import Fore, Style, init

init(autoreset=True)

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

def main():
    print_header("🧪 TESTE DE CACHE - DatabaseCache")
    
    # Teste 1: Salvar e recuperar valor simples
    print_header("TESTE 1: Salvar e Recuperar Valor Simples")
    
    test_key = "test_key_123"
    test_value = "test_value_456"
    
    print_info(f"Salvando: {test_key} = {test_value}")
    cache.set(test_key, test_value, timeout=None)
    
    print_info("Recuperando valor...")
    retrieved_value = cache.get(test_key)
    
    if retrieved_value == test_value:
        print_success(f"Valor recuperado corretamente: {retrieved_value}")
    else:
        print_error(f"Valor diferente! Esperado: {test_value}, Recebido: {retrieved_value}")
        return False
    
    # Teste 2: Salvar e recuperar dicionário
    print_header("TESTE 2: Salvar e Recuperar Dicionário")
    
    test_dict_key = "test_dict_key"
    test_dict_value = {
        'user_id': 1,
        'token': 'abc123xyz',
        'created_at': '2025-01-23T10:00:00'
    }
    
    print_info(f"Salvando dicionário: {test_dict_value}")
    cache.set(test_dict_key, test_dict_value, timeout=None)
    
    print_info("Recuperando dicionário...")
    retrieved_dict = cache.get(test_dict_key)
    
    if retrieved_dict == test_dict_value:
        print_success(f"Dicionário recuperado corretamente")
        print_info(f"Conteúdo: {retrieved_dict}")
    else:
        print_error(f"Dicionário diferente!")
        print_error(f"Esperado: {test_dict_value}")
        print_error(f"Recebido: {retrieved_dict}")
        return False
    
    # Teste 3: Sobrescrever valor
    print_header("TESTE 3: Sobrescrever Valor")
    
    print_info("Salvando valor inicial...")
    cache.set(test_key, "valor_inicial", timeout=None)
    valor1 = cache.get(test_key)
    print_info(f"Valor 1: {valor1}")
    
    print_info("Sobrescrevendo com novo valor...")
    cache.set(test_key, "valor_novo", timeout=None)
    valor2 = cache.get(test_key)
    print_info(f"Valor 2: {valor2}")
    
    if valor2 == "valor_novo":
        print_success("Sobrescrita funcionou corretamente")
    else:
        print_error(f"Sobrescrita falhou! Esperado: valor_novo, Recebido: {valor2}")
        return False
    
    # Teste 4: Deletar valor
    print_header("TESTE 4: Deletar Valor")
    
    print_info("Deletando valor...")
    cache.delete(test_key)
    
    print_info("Tentando recuperar valor deletado...")
    deleted_value = cache.get(test_key)
    
    if deleted_value is None:
        print_success("Valor foi deletado corretamente")
    else:
        print_error(f"Valor ainda existe! Recebido: {deleted_value}")
        return False
    
    # Teste 5: Simular sessão de usuário
    print_header("TESTE 5: Simular Sessão de Usuário")
    
    user_id = 999
    session_key = f"user_session:{user_id}"
    
    # Primeira sessão
    token1 = "token_celular_abc123"
    session_data1 = {
        'session_id': 'session_1',
        'user_id': user_id,
        'token': token1,
        'created_at': '2025-01-23T10:00:00'
    }
    
    print_info(f"Criando sessão 1 (CELULAR): {token1[:20]}...")
    cache.set(session_key, session_data1, timeout=None)
    
    saved_session1 = cache.get(session_key)
    print_info(f"Sessão 1 salva: {saved_session1['token'][:20]}...")
    
    # Segunda sessão (deve sobrescrever)
    token2 = "token_computador_xyz789"
    session_data2 = {
        'session_id': 'session_2',
        'user_id': user_id,
        'token': token2,
        'created_at': '2025-01-23T10:05:00'
    }
    
    print_info(f"Criando sessão 2 (COMPUTADOR): {token2[:20]}...")
    cache.set(session_key, session_data2, timeout=None)
    
    saved_session2 = cache.get(session_key)
    print_info(f"Sessão 2 salva: {saved_session2['token'][:20]}...")
    
    # Verificar se sessão 1 foi sobrescrita
    if saved_session2['token'] == token2:
        print_success("Sessão foi sobrescrita corretamente!")
        print_success(f"Token atual: {saved_session2['token'][:20]}...")
    else:
        print_error("Sessão NÃO foi sobrescrita!")
        print_error(f"Esperado: {token2[:20]}...")
        print_error(f"Recebido: {saved_session2['token'][:20]}...")
        return False
    
    # Limpar teste
    cache.delete(session_key)
    
    # RESULTADO FINAL
    print_header("📊 RESULTADO FINAL")
    print_success("✅ TODOS OS TESTES PASSARAM!")
    print_success("✅ DatabaseCache está funcionando corretamente")
    print()
    print(f"{Fore.GREEN}{'='*80}")
    print(f"{Fore.GREEN}CACHE FUNCIONANDO PERFEITAMENTE!")
    print(f"{Fore.GREEN}{'='*80}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
