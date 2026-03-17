#!/usr/bin/env python
"""
Limpeza completa de órfãos no sistema
Remove: schemas, lojas vazias, usuários, financeiros órfãos
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection, transaction
from django.contrib.auth.models import User
from superadmin.models import Loja, FinanceiroLoja


def limpar_schemas_orfaos(schemas_orfaos):
    """Remove schemas PostgreSQL órfãos"""
    if not schemas_orfaos:
        print("✅ Nenhum schema órfão para remover")
        return 0
    
    print(f"\n🗑️  Removendo {len(schemas_orfaos)} schema(s) órfão(s)...")
    
    removidos = 0
    for schema in schemas_orfaos:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            print(f"   ✅ Schema removido: {schema}")
            removidos += 1
        except Exception as e:
            print(f"   ❌ Erro ao remover {schema}: {e}")
    
    return removidos


def limpar_lojas_vazias(lojas_vazias):
    """Remove lojas com schemas vazios"""
    if not lojas_vazias:
        print("✅ Nenhuma loja vazia para remover")
        return 0
    
    print(f"\n🗑️  Removendo {len(lojas_vazias)} loja(s) com schema vazio...")
    
    removidos = 0
    for loja_id, slug, nome, schema in lojas_vazias:
        try:
            loja = Loja.objects.get(id=loja_id)
            
            # Remover schema
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            
            # Remover loja (signal remove owner se órfão)
            loja.delete()
            
            print(f"   ✅ Loja removida: {slug} (ID: {loja_id})")
            removidos += 1
        except Exception as e:
            print(f"   ❌ Erro ao remover loja {slug}: {e}")
    
    return removidos



def limpar_usuarios_orfaos(usuarios_orfaos):
    """Remove usuários órfãos (sem lojas)"""
    if not usuarios_orfaos:
        print("✅ Nenhum usuário órfão para remover")
        return 0
    
    print(f"\n🗑️  Removendo {len(usuarios_orfaos)} usuário(s) órfão(s)...")
    
    removidos = 0
    for user_id, username, email in usuarios_orfaos:
        try:
            user = User.objects.get(id=user_id)
            
            # Verificar se não é superuser/staff
            if user.is_superuser or user.is_staff:
                print(f"   ⚠️  Pulando {username} (superuser/staff)")
                continue
            
            # Verificar se não tem lojas
            if user.lojas_owned.exists():
                print(f"   ⚠️  Pulando {username} (tem lojas)")
                continue
            
            user.delete()
            print(f"   ✅ Usuário removido: {username} ({email})")
            removidos += 1
        except Exception as e:
            print(f"   ❌ Erro ao remover usuário {username}: {e}")
    
    return removidos


def limpar_financeiros_orfaos(financeiros_orfaos):
    """Remove financeiros órfãos (sem loja)"""
    if not financeiros_orfaos:
        print("✅ Nenhum financeiro órfão para remover")
        return 0
    
    print(f"\n🗑️  Removendo {len(financeiros_orfaos)} financeiro(s) órfão(s)...")
    
    removidos = 0
    for fin_id, loja_id in financeiros_orfaos:
        try:
            financeiro = FinanceiroLoja.objects.get(id=fin_id)
            financeiro.delete()
            print(f"   ✅ Financeiro removido: ID {fin_id} (loja {loja_id})")
            removidos += 1
        except Exception as e:
            print(f"   ❌ Erro ao remover financeiro {fin_id}: {e}")
    
    return removidos


def main():
    print("\n" + "="*80)
    print("LIMPEZA COMPLETA DE ÓRFÃOS NO SISTEMA")
    print("="*80 + "\n")
    
    # Importar análise
    from analisar_orfaos_completo import analisar_orfaos
    
    # Analisar órfãos
    orfaos = analisar_orfaos()
    
    total_orfaos = (
        len(orfaos['schemas_orfaos']) + 
        len(orfaos['lojas_vazias']) + 
        len(orfaos['usuarios_orfaos']) + 
        len(orfaos['financeiros_orfaos'])
    )
    
    if total_orfaos == 0:
        print("✅ Sistema limpo - nada a fazer!")
        return
    
    # Confirmar
    print("\n" + "="*80)
    print("⚠️  ATENÇÃO: Esta operação é IRREVERSÍVEL!")
    print("="*80)
    print(f"\nSerão removidos:")
    print(f"  - {len(orfaos['schemas_orfaos'])} schema(s) órfão(s)")
    print(f"  - {len(orfaos['lojas_vazias'])} loja(s) com schema vazio")
    print(f"  - {len(orfaos['usuarios_orfaos'])} usuário(s) órfão(s)")
    print(f"  - {len(orfaos['financeiros_orfaos'])} financeiro(s) órfão(s)")
    print()
    
    confirmar = input("Digite 'CONFIRMAR' para prosseguir: ")
    
    if confirmar != 'CONFIRMAR':
        print("\n❌ Operação cancelada pelo usuário")
        return
    
    print("\n" + "="*80)
    print("INICIANDO LIMPEZA")
    print("="*80)
    
    # Executar limpeza
    schemas_removidos = limpar_schemas_orfaos(orfaos['schemas_orfaos'])
    lojas_removidas = limpar_lojas_vazias(orfaos['lojas_vazias'])
    usuarios_removidos = limpar_usuarios_orfaos(orfaos['usuarios_orfaos'])
    financeiros_removidos = limpar_financeiros_orfaos(orfaos['financeiros_orfaos'])
    
    # Resumo
    print("\n" + "="*80)
    print("RESUMO DA LIMPEZA")
    print("="*80)
    print(f"Schemas removidos: {schemas_removidos}")
    print(f"Lojas removidas: {lojas_removidas}")
    print(f"Usuários removidos: {usuarios_removidos}")
    print(f"Financeiros removidos: {financeiros_removidos}")
    print()
    
    total_removidos = schemas_removidos + lojas_removidas + usuarios_removidos + financeiros_removidos
    
    if total_removidos > 0:
        print(f"✅ LIMPEZA CONCLUÍDA: {total_removidos} órfão(s) removido(s)")
    else:
        print("⚠️  Nenhum órfão foi removido")
    
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
