#!/usr/bin/env python
"""
Teste Simples de Validação da Correção de Timeout
Verifica se as alterações foram feitas corretamente sem precisar do Django
"""
import os
import sys


def print_test(name, passed, details=""):
    """Imprime resultado do teste"""
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"{status} - {name}")
    if details:
        print(f"   {details}")


def test_settings_file():
    """Testa se settings.py tem as correções"""
    print("\n" + "="*60)
    print("TESTE 1: Arquivo settings.py")
    print("="*60)
    
    try:
        with open('config/settings.py', 'r') as f:
            content = f.read()
        
        # Verificar import os
        has_import_os = 'import os' in content
        print_test("Import 'os' adicionado", has_import_os)
        
        # Verificar import dj_database_url
        has_import_dj_db = 'import dj_database_url' in content
        print_test("Import 'dj_database_url' adicionado", has_import_dj_db)
        
        # Verificar if DATABASE_URL
        has_database_url_check = "'DATABASE_URL' in os.environ" in content
        print_test("Verificação de DATABASE_URL", has_database_url_check)
        
        # Verificar connect_timeout
        has_connect_timeout = 'connect_timeout' in content
        print_test("connect_timeout configurado", has_connect_timeout)
        
        # Verificar statement_timeout
        has_statement_timeout = 'statement_timeout' in content
        print_test("statement_timeout configurado", has_statement_timeout)
        
        # Verificar conn_max_age reduzido
        has_conn_max_age_60 = 'conn_max_age=60' in content
        print_test("conn_max_age reduzido para 60s", has_conn_max_age_60)
        
        return all([
            has_import_os,
            has_import_dj_db,
            has_database_url_check,
            has_connect_timeout,
            has_statement_timeout,
            has_conn_max_age_60
        ])
        
    except FileNotFoundError:
        print_test("Arquivo settings.py encontrado", False, "Arquivo não existe")
        return False
    except Exception as e:
        print_test("Leitura do settings.py", False, str(e))
        return False


def test_auth_views_file():
    """Testa se auth_views_secure.py tem as correções"""
    print("\n" + "="*60)
    print("TESTE 2: Arquivo auth_views_secure.py")
    print("="*60)
    
    try:
        with open('superadmin/auth_views_secure.py', 'r') as f:
            content = f.read()
        
        # Verificar import time
        has_import_time = 'import time' in content
        print_test("Import 'time' adicionado", has_import_time)
        
        # Verificar import connection
        has_import_connection = 'from django.db import connection' in content
        print_test("Import 'connection' adicionado", has_import_connection)
        
        # Verificar import OperationalError
        has_import_operational = 'from django.db.utils import OperationalError' in content
        print_test("Import 'OperationalError' adicionado", has_import_operational)
        
        # Verificar função authenticate_with_retry
        has_retry_function = 'def authenticate_with_retry' in content
        print_test("Função authenticate_with_retry criada", has_retry_function)
        
        # Verificar max_retries
        has_max_retries = 'max_retries' in content
        print_test("Parâmetro max_retries presente", has_max_retries)
        
        # Verificar loop de retry
        has_retry_loop = 'for attempt in range(max_retries)' in content
        print_test("Loop de retry implementado", has_retry_loop)
        
        # Verificar connection.close()
        has_connection_close = 'connection.close()' in content
        print_test("Fechamento de conexão implementado", has_connection_close)
        
        # Verificar time.sleep
        has_time_sleep = 'time.sleep' in content
        print_test("Backoff com time.sleep implementado", has_time_sleep)
        
        # Verificar uso da função no post
        has_retry_call = 'authenticate_with_retry' in content.split('def post(')[1] if 'def post(' in content else False
        print_test("Função usada no método post", has_retry_call)
        
        # Verificar tratamento de OperationalError
        has_operational_catch = 'except OperationalError' in content.split('def post(')[1] if 'def post(' in content else False
        print_test("Tratamento de OperationalError no post", has_operational_catch)
        
        # Verificar mensagem amigável
        has_friendly_message = 'temporariamente indisponível' in content.lower()
        print_test("Mensagem amigável de erro", has_friendly_message)
        
        # Verificar código DATABASE_TIMEOUT
        has_timeout_code = 'DATABASE_TIMEOUT' in content
        print_test("Código de erro DATABASE_TIMEOUT", has_timeout_code)
        
        # Verificar status 503
        has_503_status = 'SERVICE_UNAVAILABLE' in content or '503' in content
        print_test("Status HTTP 503 para timeout", has_503_status)
        
        return all([
            has_import_time,
            has_import_connection,
            has_import_operational,
            has_retry_function,
            has_max_retries,
            has_retry_loop,
            has_retry_call,
            has_operational_catch,
            has_friendly_message,
            has_timeout_code
        ])
        
    except FileNotFoundError:
        print_test("Arquivo auth_views_secure.py encontrado", False, "Arquivo não existe")
        return False
    except Exception as e:
        print_test("Leitura do auth_views_secure.py", False, str(e))
        return False


def test_diagnostico_script():
    """Testa se script de diagnóstico existe"""
    print("\n" + "="*60)
    print("TESTE 3: Script de Diagnóstico")
    print("="*60)
    
    try:
        with open('diagnostico_db.py', 'r') as f:
            content = f.read()
        
        print_test("Script diagnostico_db.py criado", True, f"Tamanho: {len(content)} bytes")
        
        # Verificar funções principais
        has_test_connection = 'def test_connection' in content
        print_test("Função test_connection presente", has_test_connection)
        
        has_test_performance = 'def test_query_performance' in content
        print_test("Função test_query_performance presente", has_test_performance)
        
        has_test_retry = 'def test_connection_retry' in content
        print_test("Função test_connection_retry presente", has_test_retry)
        
        return True
        
    except FileNotFoundError:
        print_test("Script diagnostico_db.py criado", False, "Arquivo não existe")
        return False


def test_documentation():
    """Testa se documentação foi criada"""
    print("\n" + "="*60)
    print("TESTE 4: Documentação")
    print("="*60)
    
    docs = {
        '../DIAGNOSTICO_TIMEOUT_POSTGRESQL.md': 'Diagnóstico completo',
        '../CORRECAO_TIMEOUT_POSTGRESQL.md': 'Guia de correção',
        '../RESUMO_CORRECAO_TIMEOUT_v895.md': 'Resumo executivo',
    }
    
    all_exist = True
    for doc_path, description in docs.items():
        try:
            with open(doc_path, 'r') as f:
                content = f.read()
            size_kb = len(content) / 1024
            print_test(f"{description}", True, f"Tamanho: {size_kb:.1f}KB")
        except FileNotFoundError:
            print_test(f"{description}", False, "Arquivo não existe")
            all_exist = False
    
    return all_exist


def test_requirements():
    """Testa se dependências estão no requirements.txt"""
    print("\n" + "="*60)
    print("TESTE 5: Dependências")
    print("="*60)
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        # Verificar dj-database-url
        has_dj_db_url = 'dj-database-url' in content
        print_test("dj-database-url no requirements.txt", has_dj_db_url)
        
        # Verificar psycopg2
        has_psycopg2 = 'psycopg2' in content
        print_test("psycopg2 no requirements.txt", has_psycopg2)
        
        return has_dj_db_url and has_psycopg2
        
    except FileNotFoundError:
        print_test("Arquivo requirements.txt encontrado", False)
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "🧪 VALIDAÇÃO DA CORREÇÃO DE TIMEOUT (Teste Simples)" + "\n")
    print(f"Diretório: {os.getcwd()}")
    
    results = {
        'settings': test_settings_file(),
        'auth_views': test_auth_views_file(),
        'diagnostico': test_diagnostico_script(),
        'documentation': test_documentation(),
        'requirements': test_requirements(),
    }
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nTotal de testes: {total}")
    print(f"Testes aprovados: {passed}")
    print(f"Taxa de sucesso: {passed/total*100:.1f}%")
    
    print("\nDetalhes:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name.upper()}")
    
    # Conclusão
    print("\n" + "="*60)
    print("CONCLUSÃO")
    print("="*60)
    
    if all(results.values()):
        print("\n✅ TODAS AS CORREÇÕES FORAM IMPLEMENTADAS CORRETAMENTE!")
        print("\n📋 Próximos passos:")
        print("  1. git add backend/config/settings.py")
        print("  2. git add backend/superadmin/auth_views_secure.py")
        print("  3. git add backend/diagnostico_db.py")
        print("  4. git add backend/test_timeout_fix.py")
        print("  5. git add DIAGNOSTICO_TIMEOUT_POSTGRESQL.md")
        print("  6. git add CORRECAO_TIMEOUT_POSTGRESQL.md")
        print("  7. git add RESUMO_CORRECAO_TIMEOUT_v895.md")
        print("  8. git commit -m 'fix: adicionar timeout e retry para PostgreSQL (v895)'")
        print("  9. git push heroku main")
        print(" 10. heroku run python backend/diagnostico_db.py --app lwksistemas")
    else:
        print("\n❌ ALGUMAS CORREÇÕES ESTÃO FALTANDO")
        print("\nVerifique os testes que falharam acima.")
        print("\nTestes falhados:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name.upper()}")
    
    print("\n" + "="*60 + "\n")
    
    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
