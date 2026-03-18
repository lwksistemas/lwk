#!/usr/bin/env python
"""
Script para diagnosticar problema com search_path em migrations.
"""
import os
import sys
import django

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection, connections
from django.conf import settings
from superadmin.models import Loja

def diagnosticar():
    """Diagnostica problema com search_path."""
    
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE search_path")
    print("="*80)
    
    # 1. Verificar loja 113
    try:
        loja = Loja.objects.get(id=113)
        schema_name = f"loja_{loja.slug}"
        
        print(f"\n1. LOJA 113")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Schema: {schema_name}")
        print(f"   - Database name: {loja.database_name}")
        
        # 2. Verificar configuração Django
        print(f"\n2. CONFIGURAÇÃO DJANGO")
        if loja.database_name in settings.DATABASES:
            config = settings.DATABASES[loja.database_name]
            print(f"   ✅ Config existe em settings.DATABASES")
            print(f"   - ENGINE: {config.get('ENGINE')}")
            print(f"   - SCHEMA_NAME: {config.get('SCHEMA_NAME')}")
            print(f"   - OPTIONS: {config.get('OPTIONS')}")
        else:
            print(f"   ❌ Config NÃO existe em settings.DATABASES")
        
        # 3. Testar conexão
        print(f"\n3. TESTE DE CONEXÃO")
        from core.db_config import ensure_loja_database_config
        ensure_loja_database_config(loja.database_name)
        
        conn = connections[loja.database_name]
        conn.ensure_connection()
        
        with conn.cursor() as cursor:
            # Verificar search_path
            cursor.execute('SHOW search_path')
            current_path = cursor.fetchone()[0]
            print(f"   - search_path atual: {current_path}")
            
            # Verificar se schema está no path
            if schema_name in current_path:
                print(f"   ✅ Schema '{schema_name}' está no search_path")
            else:
                print(f"   ❌ Schema '{schema_name}' NÃO está no search_path")
            
            # Tentar criar tabela de teste
            print(f"\n4. TESTE DE CRIAÇÃO DE TABELA")
            try:
                cursor.execute(f'CREATE TABLE IF NOT EXISTS test_table_{loja.id} (id SERIAL PRIMARY KEY, nome VARCHAR(100))')
                print(f"   ✅ Tabela de teste criada")
                
                # Verificar em qual schema foi criada
                cursor.execute("""
                    SELECT table_schema 
                    FROM information_schema.tables 
                    WHERE table_name = %s
                """, [f'test_table_{loja.id}'])
                result = cursor.fetchone()
                if result:
                    schema_criado = result[0]
                    print(f"   - Tabela criada no schema: {schema_criado}")
                    if schema_criado == schema_name:
                        print(f"   ✅ Tabela criada no schema CORRETO!")
                    else:
                        print(f"   ❌ Tabela criada no schema ERRADO! (esperado: {schema_name})")
                
                # Limpar tabela de teste
                cursor.execute(f'DROP TABLE IF EXISTS test_table_{loja.id}')
                print(f"   ✅ Tabela de teste removida")
                
            except Exception as e:
                print(f"   ❌ Erro ao criar tabela de teste: {e}")
        
        # 5. Verificar tabelas em public
        print(f"\n5. TABELAS EM PUBLIC")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND (
                    table_name LIKE 'crm_vendas_%' OR
                    table_name LIKE 'stores_%' OR
                    table_name LIKE 'products_%'
                )
                ORDER BY table_name
            """)
            tabelas_public = [r[0] for r in cursor.fetchall()]
            
            if tabelas_public:
                print(f"   ⚠️  Encontradas {len(tabelas_public)} tabela(s) de apps em 'public':")
                for t in tabelas_public[:10]:
                    print(f"      - {t}")
                if len(tabelas_public) > 10:
                    print(f"      ... e mais {len(tabelas_public) - 10} tabela(s)")
            else:
                print(f"   ✅ Nenhuma tabela de apps em 'public'")
        
        # 6. Verificar backend customizado
        print(f"\n6. BACKEND CUSTOMIZADO")
        wrapper_class = conn.__class__
        print(f"   - Classe: {wrapper_class.__module__}.{wrapper_class.__name__}")
        print(f"   - Tem get_new_connection: {hasattr(wrapper_class, 'get_new_connection')}")
        print(f"   - Tem init_connection_state: {hasattr(wrapper_class, 'init_connection_state')}")
        
    except Loja.DoesNotExist:
        print("❌ Loja 113 não encontrada")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnosticar()
