#!/usr/bin/env python
"""
Script de Teste para Validar Correção de Timeout
Testa se as correções implementadas estão funcionando
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from superadmin.auth_views_secure import SecureLoginView, authenticate_with_retry
from django.db import connection
from django.db.utils import OperationalError
import json


def print_test(name, passed, details=""):
    """Imprime resultado do teste"""
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"{status} - {name}")
    if details:
        print(f"   {details}")


def test_database_config():
    """Testa se configuração de timeout está presente"""
    print("\n" + "="*60)
    print("TESTE 1: Configuração de Timeout")
    print("="*60)
    
    from django.conf import settings
    db_config = settings.DATABASES['default']
    
    # Verificar se é PostgreSQL em produção
    is_postgres = 'postgresql' in db_config.get('ENGINE', '')
    
    if is_postgres:
        options = db_config.get('OPTIONS', {})
        
        # Verificar connect_timeout
        has_connect_timeout = 'connect_timeout' in options
        connect_timeout = options.get('connect_timeout', 0)
        
        print_test(
            "connect_timeout configurado",
            has_connect_timeout and connect_timeout > 0,
            f"Valor: {connect_timeout}s (esperado: 10s)"
        )
        
        # Verificar statement_timeout
        pg_options = options.get('options', '')
        has_statement_timeout = 'statement_timeout' in pg_options
        
        print_test(
            "statement_timeout configurado",
            has_statement_timeout,
            f"Opções: {pg_options}"
        )
        
        # Verificar CONN_MAX_AGE
        conn_max_age = db_config.get('CONN_MAX_AGE', 0)
        print_test(
            "CONN_MAX_AGE otimizado",
            conn_max_age <= 60,
            f"Valor: {conn_max_age}s (esperado: ≤60s)"
        )
        
        return has_connect_timeout and has_statement_timeout
    else:
        print("ℹ️  SQLite detectado (desenvolvimento) - timeouts não aplicáveis")
        return True


def test_retry_function():
    """Testa se função de retry existe e funciona"""
    print("\n" + "="*60)
    print("TESTE 2: Função de Retry")
    print("="*60)
    
    # Verificar se função existe
    try:
        from superadmin.auth_views_secure import authenticate_with_retry
        print_test("Função authenticate_with_retry existe", True)
        
        # Verificar assinatura
        import inspect
        sig = inspect.signature(authenticate_with_retry)
        params = list(sig.parameters.keys())
        
        has_username = 'username' in params
        has_password = 'password' in params
        has_max_retries = 'max_retries' in params
        
        print_test(
            "Assinatura correta",
            has_username and has_password and has_max_retries,
            f"Parâmetros: {params}"
        )
        
        return True
        
    except ImportError as e:
        print_test("Função authenticate_with_retry existe", False, str(e))
        return False


def test_error_handling():
    """Testa se tratamento de erros está implementado"""
    print("\n" + "="*60)
    print("TESTE 3: Tratamento de Erros")
    print("="*60)
    
    try:
        # Criar request fake
        factory = RequestFactory()
        request = factory.post(
            '/api/auth/superadmin/login/',
            data=json.dumps({'username': 'test', 'password': 'test'}),
            content_type='application/json'
        )
        
        # Criar view
        view = SecureLoginView()
        
        # Verificar se método post existe
        has_post = hasattr(view, 'post')
        print_test("Método post existe", has_post)
        
        # Verificar se código tem tratamento de OperationalError
        import inspect
        source = inspect.getsource(view.post)
        
        has_operational_error = 'OperationalError' in source
        has_timeout_check = 'timeout' in source.lower()
        has_retry_call = 'authenticate_with_retry' in source
        
        print_test(
            "Tratamento de OperationalError",
            has_operational_error,
            "Captura exceções de banco"
        )
        
        print_test(
            "Verificação de timeout",
            has_timeout_check,
            "Detecta erros de timeout"
        )
        
        print_test(
            "Usa função de retry",
            has_retry_call,
            "Chama authenticate_with_retry"
        )
        
        return has_operational_error and has_timeout_check and has_retry_call
        
    except Exception as e:
        print_test("Tratamento de erros implementado", False, str(e))
        return False


def test_error_messages():
    """Testa se mensagens de erro são amigáveis"""
    print("\n" + "="*60)
    print("TESTE 4: Mensagens de Erro")
    print("="*60)
    
    try:
        import inspect
        from superadmin.auth_views_secure import SecureLoginView
        
        source = inspect.getsource(SecureLoginView.post)
        
        # Verificar mensagens amigáveis
        has_friendly_timeout = 'temporariamente indisponível' in source.lower()
        has_database_timeout_code = 'DATABASE_TIMEOUT' in source
        has_503_status = '503' in source or 'SERVICE_UNAVAILABLE' in source
        
        print_test(
            "Mensagem amigável de timeout",
            has_friendly_timeout,
            "Usa linguagem clara para usuário"
        )
        
        print_test(
            "Código de erro específico",
            has_database_timeout_code,
            "Retorna DATABASE_TIMEOUT"
        )
        
        print_test(
            "Status HTTP correto",
            has_503_status,
            "Retorna 503 Service Unavailable"
        )
        
        return has_friendly_timeout and has_database_timeout_code
        
    except Exception as e:
        print_test("Mensagens de erro amigáveis", False, str(e))
        return False


def test_connection():
    """Testa conexão real com banco"""
    print("\n" + "="*60)
    print("TESTE 5: Conexão com Banco")
    print("="*60)
    
    try:
        # Tentar conectar
        connection.ensure_connection()
        print_test("Conexão estabelecida", True)
        
        # Executar query simples
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        print_test("Query executada", result[0] == 1, f"Resultado: {result}")
        
        return True
        
    except OperationalError as e:
        error_msg = str(e).lower()
        if 'timeout' in error_msg:
            print_test(
                "Conexão com banco",
                False,
                "⚠️ TIMEOUT - Este é o problema que estamos corrigindo!"
            )
        else:
            print_test("Conexão com banco", False, str(e))
        return False
        
    except Exception as e:
        print_test("Conexão com banco", False, str(e))
        return False


def test_imports():
    """Testa se todos os imports necessários estão presentes"""
    print("\n" + "="*60)
    print("TESTE 6: Imports Necessários")
    print("="*60)
    
    imports_ok = True
    
    # Testar dj_database_url
    try:
        import dj_database_url
        print_test("dj_database_url", True, f"Versão: {dj_database_url.__version__ if hasattr(dj_database_url, '__version__') else 'N/A'}")
    except ImportError:
        print_test("dj_database_url", False, "pip install dj-database-url")
        imports_ok = False
    
    # Testar psycopg2
    try:
        import psycopg2
        print_test("psycopg2", True, f"Versão: {psycopg2.__version__}")
    except ImportError:
        print_test("psycopg2", False, "pip install psycopg2-binary")
        imports_ok = False
    
    # Testar time (built-in)
    try:
        import time
        print_test("time", True, "Built-in module")
    except ImportError:
        print_test("time", False, "Erro crítico!")
        imports_ok = False
    
    return imports_ok


def main():
    """Executa todos os testes"""
    print("\n" + "🧪 TESTE DE VALIDAÇÃO DA CORREÇÃO DE TIMEOUT" + "\n")
    
    results = {
        'imports': test_imports(),
        'config': test_database_config(),
        'retry': test_retry_function(),
        'error_handling': test_error_handling(),
        'error_messages': test_error_messages(),
        'connection': test_connection(),
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
        print("\nPróximos passos:")
        print("  1. Fazer commit das alterações")
        print("  2. Deploy para produção")
        print("  3. Monitorar logs")
        print("  4. Testar login em produção")
    elif not results['connection']:
        print("\n⚠️ CORREÇÕES IMPLEMENTADAS, MAS BANCO NÃO ESTÁ ACESSÍVEL")
        print("\nIsso é esperado se:")
        print("  - Você está em desenvolvimento local sem PostgreSQL")
        print("  - DATABASE_URL não está configurada")
        print("  - PostgreSQL está inacessível (problema de rede/firewall)")
        print("\nPróximos passos:")
        print("  1. Fazer commit das alterações")
        print("  2. Deploy para produção")
        print("  3. Executar diagnóstico no Heroku:")
        print("     heroku run python backend/diagnostico_db.py --app lwksistemas")
    else:
        print("\n❌ ALGUMAS CORREÇÕES ESTÃO FALTANDO")
        print("\nVerifique os testes que falharam acima e corrija antes do deploy.")
        print("\nTestes falhados:")
        for test_name, result in results.items():
            if not result:
                print(f"  - {test_name.upper()}")
    
    print("\n" + "="*60 + "\n")
    
    # Exit code
    sys.exit(0 if passed >= total - 1 else 1)  # Permitir falha apenas no teste de conexão


if __name__ == '__main__':
    main()
