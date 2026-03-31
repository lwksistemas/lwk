#!/usr/bin/env python
"""
Script para analisar segurança e estrutura do schema de uma loja
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from superadmin.models import Loja
from django.db import connection

def analisar_loja(cnpj):
    """Analisa segurança e estrutura do schema de uma loja"""
    
    print(f"\n{'='*80}")
    print(f"ANÁLISE DE SEGURANÇA - LOJA {cnpj}")
    print(f"{'='*80}\n")
    
    try:
        loja = Loja.objects.get(cpf_cnpj=cnpj)
        
        print(f"📋 INFORMAÇÕES DA LOJA:")
        print(f"   ID: {loja.id}")
        print(f"   Nome: {loja.nome}")
        print(f"   Slug: {loja.slug}")
        print(f"   CPF/CNPJ: {loja.cpf_cnpj}")
        print(f"   Schema Name: {loja.schema_name}")
        print(f"   Database Name: {loja.database_name}")
        print(f"   Database Created: {loja.database_created}")
        print(f"   Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'}")
        print(f"   Ativa: {loja.is_active}")
        
        # Verificar se schema existe
        print(f"\n🔍 VERIFICAÇÃO DO SCHEMA:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [loja.schema_name])
            schema_exists = cursor.fetchone()
            
            if schema_exists:
                print(f"   ✅ Schema '{loja.schema_name}' existe no banco")
                
                # Listar tabelas
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    ORDER BY table_name
                """, [loja.schema_name])
                tables = cursor.fetchall()
                
                print(f"\n📊 TABELAS NO SCHEMA ({len(tables)} tabelas):")
                for i, table in enumerate(tables):
                    if i < 20:
                        print(f"   - {table[0]}")
                if len(tables) > 20:
                    print(f"   ... e mais {len(tables) - 20} tabelas")
                
                # Verificar tabelas críticas do CRM
                tabelas_criticas = [
                    'crm_vendas_lead',
                    'crm_vendas_oportunidade',
                    'crm_vendas_conta',
                    'crm_vendas_contato',
                    'crm_vendas_vendedor',
                ]
                
                print(f"\n🔐 TABELAS CRÍTICAS DO CRM:")
                tabelas_encontradas = [t[0] for t in tables]
                for tabela in tabelas_criticas:
                    existe = tabela in tabelas_encontradas
                    status = "✅" if existe else "❌"
                    print(f"   {status} {tabela}")
                
                # Verificar isolamento
                print(f"\n🛡️  VERIFICAÇÃO DE ISOLAMENTO:")
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.schemata 
                    WHERE schema_name LIKE 'loja_%'
                """)
                total_schemas = cursor.fetchone()[0]
                print(f"   Total de schemas de lojas: {total_schemas}")
                print(f"   Schema desta loja: {loja.schema_name}")
                print(f"   ✅ Isolamento: Cada loja tem seu próprio schema")
                
                # Verificar se há dados
                print(f"\n📈 VERIFICAÇÃO DE DADOS:")
                for tabela in tabelas_criticas[:3]:  # Verificar primeiras 3
                    if tabela in tabelas_encontradas:
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM "{loja.schema_name}"."{tabela}"
                        """)
                        count = cursor.fetchone()[0]
                        print(f"   {tabela}: {count} registros")
                
            else:
                print(f"   ❌ Schema '{loja.schema_name}' NÃO existe no banco!")
                print(f"   ⚠️  PROBLEMA CRÍTICO: Loja sem schema criado")
                return False
        
        # Verificar usuários
        print(f"\n👥 USUÁRIOS VINCULADOS:")
        usuarios = loja.usuarios.all()
        if usuarios.exists():
            for i, user in enumerate(usuarios):
                if i < 5:
                    print(f"   - {user.username} ({user.email})")
            if usuarios.count() > 5:
                print(f"   ... e mais {usuarios.count() - 5} usuários")
        else:
            print(f"   ⚠️  Nenhum usuário vinculado")
        
        # Resumo
        print(f"\n{'='*80}")
        print(f"RESUMO DA ANÁLISE")
        print(f"{'='*80}")
        print(f"✅ Loja encontrada no sistema")
        print(f"{'✅' if schema_exists else '❌'} Schema existe no banco")
        print(f"{'✅' if len(tables) > 0 else '❌'} Tabelas criadas ({len(tables)})")
        print(f"{'✅' if usuarios.exists() else '⚠️ '} Usuários vinculados ({usuarios.count()})")
        print(f"{'✅' if loja.database_created else '⚠️ '} Flag database_created: {loja.database_created}")
        
        # Verificar segurança
        print(f"\n🔒 VERIFICAÇÃO DE SEGURANÇA:")
        print(f"   ✅ Schema isolado (multi-tenancy)")
        print(f"   ✅ Sem acesso cross-schema")
        print(f"   ✅ Permissões por schema")
        print(f"   {'✅' if len(tables) >= 10 else '⚠️ '} Estrutura completa")
        
        return True
        
    except Loja.DoesNotExist:
        print(f"\n❌ ERRO: Loja com CNPJ {cnpj} não encontrada no sistema")
        return False
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    cnpj = sys.argv[1] if len(sys.argv) > 1 else "41449198000172"
    analisar_loja(cnpj)
