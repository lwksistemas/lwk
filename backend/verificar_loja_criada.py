#!/usr/bin/env python
"""
Script para verificar se uma loja foi criada corretamente com tabelas isoladas.
Uso: python backend/verificar_loja_criada.py <slug_ou_id>
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection, connections
from superadmin.models import Loja

def verificar_loja(identificador):
    """Verifica se a loja foi criada corretamente."""
    
    print("\n" + "="*80)
    print("VERIFICAÇÃO DE LOJA CRIADA")
    print("="*80)
    
    try:
        # Buscar loja por ID ou slug
        try:
            loja_id = int(identificador)
            loja = Loja.objects.get(id=loja_id)
        except ValueError:
            loja = Loja.objects.get(slug=identificador)
        
        print(f"\n✅ Loja encontrada:")
        print(f"   - ID: {loja.id}")
        print(f"   - Slug: {loja.slug}")
        print(f"   - Nome: {loja.nome}")
        print(f"   - Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'}")
        print(f"   - Database: {loja.database_name}")
        print(f"   - Database Created: {loja.database_created}")
        
        schema_name = f"loja_{loja.slug}"
        
        # 1. Verificar se schema existe
        print(f"\n{'='*80}")
        print("1. VERIFICANDO SCHEMA NO POSTGRESQL")
        print("="*80)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            schema_exists = cursor.fetchone()
        
        if not schema_exists:
            print(f"❌ Schema '{schema_name}' NÃO existe no PostgreSQL")
            return False
        
        print(f"✅ Schema '{schema_name}' existe no PostgreSQL")
        
        # 2. Listar tabelas no schema
        print(f"\n{'='*80}")
        print("2. TABELAS NO SCHEMA DA LOJA")
        print("="*80)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name
            """, [schema_name])
            tabelas = cursor.fetchall()
        
        if not tabelas:
            print(f"❌ Schema '{schema_name}' está VAZIO (0 tabelas)")
            return False
        
        print(f"\n✅ Schema '{schema_name}' tem {len(tabelas)} tabela(s):\n")
        
        # Agrupar por app
        tabelas_crm = []
        tabelas_stores = []
        tabelas_products = []
        tabelas_django = []
        tabelas_outras = []
        
        for tabela, tipo in tabelas:
            if tabela.startswith('crm_vendas_'):
                tabelas_crm.append(tabela)
            elif tabela.startswith('stores_'):
                tabelas_stores.append(tabela)
            elif tabela.startswith('products_'):
                tabelas_products.append(tabela)
            elif tabela.startswith('django_'):
                tabelas_django.append(tabela)
            else:
                tabelas_outras.append(tabela)
        
        if tabelas_crm:
            print(f"📊 CRM Vendas ({len(tabelas_crm)} tabelas):")
            for t in sorted(tabelas_crm):
                print(f"   ✓ {t}")
        
        if tabelas_stores:
            print(f"\n🏪 Stores ({len(tabelas_stores)} tabelas):")
            for t in sorted(tabelas_stores):
                print(f"   ✓ {t}")
        
        if tabelas_products:
            print(f"\n📦 Products ({len(tabelas_products)} tabelas):")
            for t in sorted(tabelas_products):
                print(f"   ✓ {t}")
        
        if tabelas_django:
            print(f"\n🔧 Django ({len(tabelas_django)} tabelas):")
            for t in sorted(tabelas_django):
                print(f"   ✓ {t}")
        
        if tabelas_outras:
            print(f"\n❓ Outras ({len(tabelas_outras)} tabelas):")
            for t in sorted(tabelas_outras):
                print(f"   ✓ {t}")
        
        # 3. Verificar tabelas essenciais do CRM
        if loja.tipo_loja and loja.tipo_loja.slug == 'crm-vendas':
            print(f"\n{'='*80}")
            print("3. VERIFICANDO TABELAS ESSENCIAIS DO CRM")
            print("="*80)
            
            tabelas_essenciais = [
                'crm_vendas_vendedor',
                'crm_vendas_conta',
                'crm_vendas_contato',
                'crm_vendas_lead',
                'crm_vendas_oportunidade',
                'crm_vendas_atividade'
            ]
            
            todas_presentes = True
            for tabela in tabelas_essenciais:
                presente = tabela in [t for t, _ in tabelas]
                status = "✅" if presente else "❌"
                print(f"   {status} {tabela}")
                if not presente:
                    todas_presentes = False
            
            if not todas_presentes:
                print(f"\n⚠️  ALGUMAS tabelas essenciais do CRM estão FALTANDO!")
                return False
            
            print(f"\n✅ TODAS as tabelas essenciais do CRM estão presentes!")
        
        # 4. Verificar se há tabelas em public (vazamento)
        print(f"\n{'='*80}")
        print("4. VERIFICANDO VAZAMENTO PARA SCHEMA PUBLIC")
        print("="*80)
        
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
            tabelas_public = cursor.fetchall()
        
        if tabelas_public:
            print(f"⚠️  Encontradas {len(tabelas_public)} tabela(s) de apps em 'public':")
            for (tabela,) in tabelas_public[:10]:
                print(f"   - {tabela}")
            if len(tabelas_public) > 10:
                print(f"   ... e mais {len(tabelas_public) - 10} tabela(s)")
            print(f"\n⚠️  ATENÇÃO: Há vazamento de tabelas para o schema public!")
        else:
            print(f"✅ Nenhuma tabela de apps encontrada em 'public' (sem vazamento)")
        
        # 5. Testar conexão com o banco da loja
        print(f"\n{'='*80}")
        print("5. TESTANDO CONEXÃO COM BANCO DA LOJA")
        print("="*80)
        
        from core.db_config import ensure_loja_database_config
        
        if ensure_loja_database_config(loja.database_name):
            print(f"✅ Configuração do banco '{loja.database_name}' adicionada")
            
            try:
                conn = connections[loja.database_name]
                with conn.cursor() as cursor:
                    cursor.execute('SHOW search_path')
                    search_path = cursor.fetchone()[0]
                    print(f"✅ Search path: {search_path}")
                    
                    if schema_name in search_path:
                        print(f"✅ Schema '{schema_name}' está no search_path")
                    else:
                        print(f"⚠️  Schema '{schema_name}' NÃO está no search_path")
            except Exception as e:
                print(f"❌ Erro ao conectar: {e}")
        else:
            print(f"❌ Falha ao configurar banco '{loja.database_name}'")
        
        # Resumo final
        print(f"\n{'='*80}")
        print("RESUMO FINAL")
        print("="*80)
        print(f"Loja: {loja.nome} (ID: {loja.id})")
        print(f"Schema: {schema_name}")
        print(f"Tabelas: {len(tabelas)}")
        print(f"Vazamento para public: {'SIM ⚠️' if tabelas_public else 'NÃO ✅'}")
        
        if len(tabelas) > 0 and not tabelas_public:
            print(f"\n🎉 SUCESSO! Loja criada corretamente com isolamento de dados!")
            return True
        elif len(tabelas) > 0 and tabelas_public:
            print(f"\n⚠️  ATENÇÃO! Loja criada mas há vazamento para public!")
            return False
        else:
            print(f"\n❌ FALHA! Schema vazio ou problemas na criação!")
            return False
        
    except Loja.DoesNotExist:
        print(f"\n❌ Loja '{identificador}' não encontrada")
        return False
    except Exception as e:
        print(f"\n❌ Erro ao verificar loja: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python backend/verificar_loja_criada.py <slug_ou_id>")
        print("Exemplo: python backend/verificar_loja_criada.py 12345678000199")
        print("Exemplo: python backend/verificar_loja_criada.py 110")
        sys.exit(1)
    
    identificador = sys.argv[1]
    sucesso = verificar_loja(identificador)
    sys.exit(0 if sucesso else 1)
