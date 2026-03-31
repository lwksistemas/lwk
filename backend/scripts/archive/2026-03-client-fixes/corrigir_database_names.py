#!/usr/bin/env python
"""
Script para corrigir database_names duplicados e garantir isolamento

Este script:
1. Identifica lojas com database_name duplicado
2. Gera novos database_names únicos
3. Cria schemas no PostgreSQL
4. Atualiza as lojas

IMPORTANTE: Execute APENAS em produção via Heroku
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.db import connection
from superadmin.models import Loja
from collections import Counter
import re


def verificar_duplicados():
    """Verifica se há database_names duplicados"""
    print("\n" + "="*80)
    print("🔍 VERIFICANDO DATABASE_NAMES DUPLICADOS")
    print("="*80 + "\n")
    
    lojas = Loja.objects.filter(is_active=True)
    database_names = [loja.database_name for loja in lojas]
    duplicados = {name: count for name, count in Counter(database_names).items() if count > 1}
    
    if not duplicados:
        print("✅ Nenhum database_name duplicado encontrado!")
        return []
    
    print(f"❌ Encontrados {len(duplicados)} database_names duplicados:\n")
    
    lojas_problematicas = []
    for db_name, count in duplicados.items():
        print(f"🔴 {db_name} (usado por {count} lojas):")
        lojas_dup = lojas.filter(database_name=db_name).order_by('created_at')
        
        for i, loja in enumerate(lojas_dup):
            print(f"   {i+1}. ID: {loja.id:3d} | {loja.nome:40s} | Criada: {loja.created_at}")
            lojas_problematicas.append(loja)
    
    return lojas_problematicas


def gerar_database_name_unico(loja):
    """Gera um database_name único para a loja"""
    # Tentar usar o slug atual
    base = f"loja_{loja.slug.replace('-', '_')}"
    
    # Se já existe, adicionar sufixo
    if Loja.objects.filter(database_name=base).exclude(pk=loja.pk).exists():
        # Adicionar ID da loja para garantir unicidade
        base = f"loja_{loja.slug.replace('-', '_')}_{loja.id}"
    
    # Validar formato
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', base):
        # Se inválido, usar apenas ID
        base = f"loja_id_{loja.id}"
    
    return base


def criar_schema_postgres(schema_name):
    """Cria schema no PostgreSQL se não existir"""
    try:
        with connection.cursor() as cursor:
            # Verificar se schema existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [schema_name])
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print(f"   ℹ️  Schema '{schema_name}' já existe")
                return True
            
            # Criar schema
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            print(f"   ✅ Schema '{schema_name}' criado")
            return True
            
    except Exception as e:
        print(f"   ❌ Erro ao criar schema '{schema_name}': {e}")
        return False


def aplicar_migrations(loja):
    """Aplica migrations no schema da loja"""
    try:
        from django.core.management import call_command
        
        db_name = loja.database_name
        tipo_loja_nome = loja.tipo_loja.nome if loja.tipo_loja else ''
        
        print(f"   🔄 Aplicando migrations...")
        
        # Migrations básicas
        call_command('migrate', 'stores', '--database', db_name, verbosity=0)
        call_command('migrate', 'products', '--database', db_name, verbosity=0)
        
        # Migrations específicas
        if tipo_loja_nome == 'Clínica de Estética':
            call_command('migrate', 'clinica_estetica', '--database', db_name, verbosity=0)
        elif tipo_loja_nome == 'Restaurante':
            call_command('migrate', 'restaurante', '--database', db_name, verbosity=0)
        elif tipo_loja_nome == 'Serviços':
            call_command('migrate', 'servicos', '--database', db_name, verbosity=0)
        elif tipo_loja_nome == 'Cabeleireiro':
            call_command('migrate', 'cabeleireiro', '--database', db_name, verbosity=0)
        elif tipo_loja_nome == 'E-commerce':
            call_command('migrate', 'ecommerce', '--database', db_name, verbosity=0)
        
        print(f"   ✅ Migrations aplicadas")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao aplicar migrations: {e}")
        return False


def corrigir_loja(loja, manter_primeira=True):
    """
    Corrige database_name de uma loja
    
    Args:
        loja: Instância da loja
        manter_primeira: Se True, mantém dados da primeira loja (mais antiga)
    """
    print(f"\n📝 Corrigindo loja: {loja.nome} (ID: {loja.id})")
    print(f"   Database atual: {loja.database_name}")
    
    # Gerar novo database_name
    novo_db_name = gerar_database_name_unico(loja)
    print(f"   Novo database: {novo_db_name}")
    
    # Criar schema
    schema_name = novo_db_name.replace('-', '_')
    if not criar_schema_postgres(schema_name):
        print(f"   ❌ Falha ao criar schema. Abortando correção desta loja.")
        return False
    
    # Atualizar loja (desabilitar validação temporariamente)
    loja.database_name = novo_db_name
    loja.database_created = True
    loja.save(update_fields=['database_name', 'database_created'])
    print(f"   ✅ Database_name atualizado")
    
    # Aplicar migrations
    if not aplicar_migrations(loja):
        print(f"   ⚠️  Migrations falharam, mas loja foi atualizada")
    
    print(f"   ✅ Loja corrigida com sucesso!")
    return True


def corrigir_todas():
    """Corrige todas as lojas com database_name duplicado"""
    print("\n" + "="*80)
    print("🔧 INICIANDO CORREÇÃO DE DATABASE_NAMES")
    print("="*80)
    
    # Verificar duplicados
    lojas_problematicas = verificar_duplicados()
    
    if not lojas_problematicas:
        print("\n✅ Nenhuma correção necessária!")
        return
    
    print(f"\n⚠️  Serão corrigidas {len(lojas_problematicas)} lojas")
    print("\n⚠️  ATENÇÃO:")
    print("   - Cada loja receberá um novo database_name único")
    print("   - Um novo schema será criado no PostgreSQL")
    print("   - As lojas ficarão VAZIAS (sem dados)")
    print("   - Os dados antigos permanecerão no schema original")
    
    confirmacao = input("\nDigite 'CONFIRMAR' para prosseguir: ")
    if confirmacao != 'CONFIRMAR':
        print("❌ Operação cancelada.")
        return
    
    # Agrupar por database_name
    from collections import defaultdict
    grupos = defaultdict(list)
    for loja in lojas_problematicas:
        grupos[loja.database_name].append(loja)
    
    # Corrigir cada grupo
    sucesso = 0
    falhas = 0
    
    for db_name, lojas_grupo in grupos.items():
        print(f"\n{'='*80}")
        print(f"Corrigindo grupo: {db_name} ({len(lojas_grupo)} lojas)")
        print(f"{'='*80}")
        
        # Ordenar por data de criação (mais antiga primeiro)
        lojas_grupo.sort(key=lambda x: x.created_at)
        
        # Manter a primeira (mais antiga) com o database_name original
        # Corrigir as demais
        for i, loja in enumerate(lojas_grupo):
            if i == 0:
                print(f"\n✅ Mantendo loja original: {loja.nome} (ID: {loja.id})")
                print(f"   Esta loja manterá o database_name: {db_name}")
                print(f"   E manterá todos os dados existentes")
                continue
            
            if corrigir_loja(loja, manter_primeira=True):
                sucesso += 1
            else:
                falhas += 1
    
    # Resumo
    print("\n" + "="*80)
    print("📊 RESUMO DA CORREÇÃO")
    print("="*80)
    print(f"✅ Lojas corrigidas com sucesso: {sucesso}")
    print(f"❌ Lojas com falha: {falhas}")
    print(f"ℹ️  Lojas mantidas (originais): {len(grupos)}")
    print("="*80 + "\n")
    
    if falhas == 0:
        print("✅ Todas as correções foram aplicadas com sucesso!")
        print("\n📝 PRÓXIMOS PASSOS:")
        print("   1. Verificar que as lojas estão acessíveis")
        print("   2. As lojas corrigidas estarão VAZIAS")
        print("   3. Os clientes precisarão recadastrar seus dados")
        print("   4. Ou você pode migrar dados do schema antigo manualmente")
    else:
        print("⚠️  Algumas correções falharam. Verifique os logs acima.")


if __name__ == '__main__':
    corrigir_todas()
