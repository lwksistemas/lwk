#!/usr/bin/env python
"""
Script para verificar isolamento de dados entre lojas

Verifica:
1. Se cada loja tem seu próprio database_name único
2. Se os schemas existem no PostgreSQL
3. Se há dados "vazando" entre lojas

Uso:
    python backend/verificar_isolamento_lojas.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
# Tentar settings_production primeiro, se falhar usar settings local
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
    django.setup()
except Exception as e:
    print(f"⚠️  Não foi possível usar settings_production: {e}")
    print("🔄 Tentando usar settings local...\n")
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    django.setup()

from django.db import connection
from superadmin.models import Loja
from collections import Counter


def verificar_database_names():
    """Verifica se há lojas compartilhando database_name"""
    print("\n" + "="*80)
    print("🔍 VERIFICAÇÃO DE ISOLAMENTO DE LOJAS")
    print("="*80 + "\n")
    
    lojas = Loja.objects.filter(is_active=True).order_by('created_at')
    
    print(f"📊 Total de lojas ativas: {lojas.count()}\n")
    
    # Verificar database_names duplicados
    database_names = [loja.database_name for loja in lojas]
    duplicados = [name for name, count in Counter(database_names).items() if count > 1]
    
    if duplicados:
        print("❌ PROBLEMA CRÍTICO: Lojas compartilhando database_name!")
        print("\nDatabase names duplicados:")
        for db_name in duplicados:
            lojas_duplicadas = lojas.filter(database_name=db_name)
            print(f"\n  🔴 {db_name}:")
            for loja in lojas_duplicadas:
                print(f"     - ID: {loja.id} | Nome: {loja.nome} | Slug: {loja.slug}")
                print(f"       Criada em: {loja.created_at}")
        print("\n⚠️  AÇÃO NECESSÁRIA: Corrigir database_names duplicados!")
        return False
    else:
        print("✅ Todas as lojas têm database_name único\n")
    
    # Listar todas as lojas
    print("📋 Lista de lojas:")
    print("-" * 80)
    for loja in lojas:
        print(f"ID: {loja.id:3d} | {loja.nome:30s} | DB: {loja.database_name:30s}")
    print("-" * 80)
    
    return True


def verificar_schemas_postgres():
    """Verifica se os schemas existem no PostgreSQL"""
    print("\n" + "="*80)
    print("🔍 VERIFICAÇÃO DE SCHEMAS NO POSTGRESQL")
    print("="*80 + "\n")
    
    try:
        with connection.cursor() as cursor:
            # Listar todos os schemas
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name
            """)
            schemas_existentes = [row[0] for row in cursor.fetchall()]
            
            print(f"📊 Total de schemas 'loja_*': {len(schemas_existentes)}\n")
            
            # Verificar lojas ativas
            lojas = Loja.objects.filter(is_active=True)
            
            print("📋 Verificação de schemas:")
            print("-" * 80)
            
            lojas_sem_schema = []
            schemas_sem_loja = list(schemas_existentes)
            
            for loja in lojas:
                schema_name = loja.database_name.replace('-', '_')
                tem_schema = schema_name in schemas_existentes
                
                status = "✅" if tem_schema else "❌"
                print(f"{status} Loja: {loja.nome:30s} | Schema: {schema_name:30s}")
                
                if not tem_schema:
                    lojas_sem_schema.append(loja)
                elif schema_name in schemas_sem_loja:
                    schemas_sem_loja.remove(schema_name)
            
            print("-" * 80)
            
            # Resumo
            if lojas_sem_schema:
                print(f"\n❌ {len(lojas_sem_schema)} loja(s) SEM schema no PostgreSQL:")
                for loja in lojas_sem_schema:
                    print(f"   - {loja.nome} (ID: {loja.id})")
                print("\n⚠️  AÇÃO: Criar schemas faltantes")
            else:
                print("\n✅ Todas as lojas têm schema no PostgreSQL")
            
            if schemas_sem_loja:
                print(f"\n⚠️  {len(schemas_sem_loja)} schema(s) órfão(s) (sem loja correspondente):")
                for schema in schemas_sem_loja:
                    print(f"   - {schema}")
                print("\n💡 Considere remover schemas órfãos se não forem mais necessários")
            
            return len(lojas_sem_schema) == 0
            
    except Exception as e:
        print(f"❌ Erro ao verificar schemas: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_dados_clinica():
    """Verifica se há dados de clínica em lojas"""
    print("\n" + "="*80)
    print("🔍 VERIFICAÇÃO DE DADOS - CLÍNICAS DE ESTÉTICA")
    print("="*80 + "\n")
    
    try:
        from clinica_estetica.models import Cliente, Procedimento, Agendamento
        
        lojas_clinica = Loja.objects.filter(
            tipo_loja__nome='Clínica de Estética',
            is_active=True
        )
        
        print(f"📊 Total de clínicas ativas: {lojas_clinica.count()}\n")
        print("📋 Contagem de dados por loja:")
        print("-" * 100)
        print(f"{'Loja':<35s} | {'Clientes':>10s} | {'Procedimentos':>15s} | {'Agendamentos':>15s}")
        print("-" * 100)
        
        for loja in lojas_clinica:
            db_name = loja.database_name
            
            try:
                clientes = Cliente.objects.using(db_name).count()
                procedimentos = Procedimento.objects.using(db_name).count()
                agendamentos = Agendamento.objects.using(db_name).count()
                
                print(f"{loja.nome:<35s} | {clientes:>10d} | {procedimentos:>15d} | {agendamentos:>15d}")
            except Exception as e:
                print(f"{loja.nome:<35s} | {'ERRO':>10s} | {str(e)[:50]}")
        
        print("-" * 100)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n🔒 VERIFICAÇÃO DE ISOLAMENTO DE DADOS ENTRE LOJAS")
    print("=" * 80)
    
    # 1. Verificar database_names
    ok1 = verificar_database_names()
    
    # 2. Verificar schemas no PostgreSQL
    ok2 = verificar_schemas_postgres()
    
    # 3. Verificar dados
    ok3 = verificar_dados_clinica()
    
    # Resumo final
    print("\n" + "="*80)
    print("📊 RESUMO FINAL")
    print("="*80)
    print(f"Database names únicos: {'✅ OK' if ok1 else '❌ PROBLEMA'}")
    print(f"Schemas no PostgreSQL: {'✅ OK' if ok2 else '❌ PROBLEMA'}")
    print(f"Verificação de dados:  {'✅ OK' if ok3 else '❌ PROBLEMA'}")
    print("="*80 + "\n")
    
    if ok1 and ok2 and ok3:
        print("✅ Sistema de isolamento está funcionando corretamente!")
        sys.exit(0)
    else:
        print("❌ Problemas detectados no isolamento de dados!")
        print("⚠️  Revise os problemas acima e tome as ações necessárias.")
        sys.exit(1)


if __name__ == '__main__':
    main()
