#!/usr/bin/env python
"""
Script para listar todos os usuários do tipo superadmin e suporte
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

def listar_usuarios():
    """Lista todos os usuários superadmin e suporte"""
    print("\n" + "="*80)
    print("USUÁRIOS DO SISTEMA (SuperAdmin e Suporte)")
    print("="*80 + "\n")
    
    # Buscar todos os usuários do sistema
    usuarios = UsuarioSistema.objects.select_related('user').all()
    
    if not usuarios.exists():
        print("❌ Nenhum usuário do sistema encontrado.\n")
        return
    
    # Separar por tipo
    superadmins = usuarios.filter(tipo='superadmin')
    suportes = usuarios.filter(tipo='suporte')
    
    # Mostrar SuperAdmins
    print(f"🔐 SUPER ADMINS ({superadmins.count()})")
    print("-" * 80)
    for usuario in superadmins:
        user = usuario.user
        print(f"  ID: {usuario.id}")
        print(f"  Username: {user.username}")
        print(f"  Nome: {user.first_name} {user.last_name}".strip())
        print(f"  Email: {user.email}")
        print(f"  Telefone: {usuario.telefone or 'N/A'}")
        print(f"  Ativo: {'✅ Sim' if usuario.is_active else '❌ Não'}")
        print(f"  Senha Provisória: {'✅ Sim' if usuario.senha_provisoria else '❌ Não'}")
        print(f"  Senha Alterada: {'✅ Sim' if usuario.senha_foi_alterada else '❌ Não'}")
        print(f"  Permissões:")
        print(f"    - Criar Lojas: {'✅' if usuario.pode_criar_lojas else '❌'}")
        print(f"    - Gerenciar Financeiro: {'✅' if usuario.pode_gerenciar_financeiro else '❌'}")
        print(f"    - Acessar Todas Lojas: {'✅' if usuario.pode_acessar_todas_lojas else '❌'}")
        print(f"  Criado em: {usuario.created_at.strftime('%d/%m/%Y %H:%M')}")
        print("-" * 80)
    
    # Mostrar Suportes
    if suportes.exists():
        print(f"\n🛠️ SUPORTE ({suportes.count()})")
        print("-" * 80)
        for usuario in suportes:
            user = usuario.user
            lojas_acesso = usuario.lojas_acesso.count()
            print(f"  ID: {usuario.id}")
            print(f"  Username: {user.username}")
            print(f"  Nome: {user.first_name} {user.last_name}".strip())
            print(f"  Email: {user.email}")
            print(f"  Telefone: {usuario.telefone or 'N/A'}")
            print(f"  Ativo: {'✅ Sim' if usuario.is_active else '❌ Não'}")
            print(f"  Senha Provisória: {'✅ Sim' if usuario.senha_provisoria else '❌ Não'}")
            print(f"  Senha Alterada: {'✅ Sim' if usuario.senha_foi_alterada else '❌ Não'}")
            print(f"  Lojas com Acesso: {lojas_acesso}")
            print(f"  Permissões:")
            print(f"    - Criar Lojas: {'✅' if usuario.pode_criar_lojas else '❌'}")
            print(f"    - Gerenciar Financeiro: {'✅' if usuario.pode_gerenciar_financeiro else '❌'}")
            print(f"    - Acessar Todas Lojas: {'✅' if usuario.pode_acessar_todas_lojas else '❌'}")
            print(f"  Criado em: {usuario.created_at.strftime('%d/%m/%Y %H:%M')}")
            print("-" * 80)
    
    # Resumo
    print(f"\n📊 RESUMO")
    print("-" * 80)
    print(f"  Total de Usuários: {usuarios.count()}")
    print(f"  Super Admins: {superadmins.count()}")
    print(f"  Suporte: {suportes.count()}")
    print(f"  Ativos: {usuarios.filter(is_active=True).count()}")
    print(f"  Inativos: {usuarios.filter(is_active=False).count()}")
    print("-" * 80 + "\n")

if __name__ == '__main__':
    try:
        listar_usuarios()
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
