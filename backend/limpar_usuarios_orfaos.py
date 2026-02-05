#!/usr/bin/env python
"""
Script para limpar usuários órfãos do Django (User sem UsuarioSistema ou Loja)

Uso:
    python limpar_usuarios_orfaos.py [--dry-run]
    
    --dry-run: Apenas lista os usuários órfãos sem removê-los
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection, transaction
from superadmin.models import UsuarioSistema, Loja


def limpar_usuarios_orfaos(dry_run=False):
    """
    Remove usuários do Django que não têm UsuarioSistema ou Loja associados
    
    Args:
        dry_run: Se True, apenas lista os órfãos sem remover
    """
    print("🔍 Buscando usuários órfãos...")
    print("-" * 60)
    
    usuarios_orfaos = []
    total_users = User.objects.count()
    
    for user in User.objects.all():
        # Verificar se tem UsuarioSistema
        tem_perfil_sistema = UsuarioSistema.objects.filter(user=user).exists()
        
        # Verificar se é owner de alguma loja
        tem_loja = Loja.objects.filter(owner=user).exists()
        
        # Se não tem nenhum dos dois, é órfão
        if not tem_perfil_sistema and not tem_loja:
            usuarios_orfaos.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined
            })
    
    print(f"📊 Total de usuários: {total_users}")
    print(f"🔴 Usuários órfãos encontrados: {len(usuarios_orfaos)}")
    print("-" * 60)
    
    if not usuarios_orfaos:
        print("✅ Nenhum usuário órfão encontrado!")
        return
    
    # Listar órfãos
    print("\n📋 Lista de usuários órfãos:")
    for i, orfao in enumerate(usuarios_orfaos, 1):
        print(f"\n{i}. Username: {orfao['username']}")
        print(f"   ID: {orfao['id']}")
        print(f"   Email: {orfao['email']}")
        print(f"   Superuser: {orfao['is_superuser']}")
        print(f"   Staff: {orfao['is_staff']}")
        print(f"   Cadastrado em: {orfao['date_joined']}")
    
    if dry_run:
        print("\n⚠️ Modo DRY-RUN: Nenhum usuário foi removido")
        print("Execute sem --dry-run para remover os usuários órfãos")
        return
    
    # Confirmar remoção
    print("\n" + "=" * 60)
    resposta = input(f"⚠️ Deseja remover {len(usuarios_orfaos)} usuário(s) órfão(s)? (sim/não): ")
    
    if resposta.lower() not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada pelo usuário")
        return
    
    # Remover órfãos
    print("\n🗑️ Removendo usuários órfãos...")
    removidos = 0
    erros = 0
    
    for orfao in usuarios_orfaos:
        try:
            with transaction.atomic():
                user = User.objects.get(id=orfao['id'])
                
                # Remover tokens JWT se existirem
                try:
                    cursor = connection.cursor()
                    cursor.execute(
                        'DELETE FROM token_blacklist_outstandingtoken WHERE user_id = %s',
                        [user.id]
                    )
                    tokens_removidos = cursor.rowcount
                    if tokens_removidos > 0:
                        print(f"  🔑 Removidos {tokens_removidos} token(s) de {user.username}")
                except Exception as e:
                    print(f"  ⚠️ Erro ao remover tokens de {user.username}: {e}")
                
                # Remover usuário
                user.delete()
                print(f"  ✅ Removido: {orfao['username']} (ID: {orfao['id']})")
                removidos += 1
                
        except Exception as e:
            print(f"  ❌ Erro ao remover {orfao['username']}: {e}")
            erros += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Usuários removidos: {removidos}")
    if erros > 0:
        print(f"❌ Erros: {erros}")
    print("=" * 60)


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("🔍 Modo DRY-RUN ativado (apenas listagem)")
        print("=" * 60)
    
    limpar_usuarios_orfaos(dry_run=dry_run)
