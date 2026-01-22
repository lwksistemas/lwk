#!/usr/bin/env python3
"""
Script de auditoria de segurança para verificar permissões
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import UsuarioSistema

def auditoria_seguranca():
    """Executa auditoria de segurança do sistema"""
    print("🔒 AUDITORIA DE SEGURANÇA - LWK SISTEMAS")
    print("=" * 60)
    
    # 1. Verificar superusers
    superusers = User.objects.filter(is_superuser=True, is_active=True)
    print(f"\n👑 SUPERUSERS ATIVOS ({superusers.count()}):")
    for user in superusers:
        print(f"   ✅ {user.username} ({user.email}) - Último login: {user.last_login}")
    
    # 2. Verificar usuários com acesso de staff
    staff_users = User.objects.filter(is_staff=True, is_active=True, is_superuser=False)
    print(f"\n👨‍💼 USUÁRIOS STAFF ({staff_users.count()}):")
    for user in staff_users:
        print(f"   ⚠️  {user.username} ({user.email}) - Staff sem superuser")
    
    # 3. Verificar usuários de loja
    usuarios_loja = UsuarioSistema.objects.filter(is_active=True).select_related('user', 'loja')
    print(f"\n🏪 USUÁRIOS DE LOJA ({usuarios_loja.count()}):")
    for usuario in usuarios_loja:
        loja_nome = usuario.loja.nome if usuario.loja else "SEM LOJA"
        is_superuser = "⚠️ SUPERUSER!" if usuario.user.is_superuser else "✅ Normal"
        print(f"   {usuario.user.username} - {loja_nome} - {is_superuser}")
    
    # 4. Verificar usuários órfãos (sem UsuarioSistema)
    usuarios_orfaos = User.objects.filter(
        is_active=True,
        is_superuser=False
    ).exclude(
        id__in=usuarios_loja.values_list('user_id', flat=True)
    )
    
    print(f"\n👻 USUÁRIOS ÓRFÃOS ({usuarios_orfaos.count()}):")
    for user in usuarios_orfaos:
        print(f"   ⚠️  {user.username} ({user.email}) - Sem UsuarioSistema")
    
    # 5. Verificar problemas de segurança
    problemas = []
    
    # Usuários de loja com privilégios de superuser
    usuarios_loja_superuser = usuarios_loja.filter(user__is_superuser=True)
    if usuarios_loja_superuser.exists():
        problemas.append(f"🚨 {usuarios_loja_superuser.count()} usuários de loja com privilégios de superuser")
    
    # Usuários staff sem superuser
    if staff_users.exists():
        problemas.append(f"⚠️  {staff_users.count()} usuários com is_staff=True mas não superuser")
    
    # Usuários órfãos
    if usuarios_orfaos.exists():
        problemas.append(f"👻 {usuarios_orfaos.count()} usuários órfãos sem UsuarioSistema")
    
    print(f"\n🔍 RESUMO DA AUDITORIA:")
    print("=" * 60)
    
    if problemas:
        print("❌ PROBLEMAS ENCONTRADOS:")
        for problema in problemas:
            print(f"   {problema}")
        
        print(f"\n🔧 AÇÕES RECOMENDADAS:")
        if usuarios_loja_superuser.exists():
            print("   1. Remover privilégios de superuser dos usuários de loja")
        if staff_users.exists():
            print("   2. Revisar usuários com is_staff=True")
        if usuarios_orfaos.exists():
            print("   3. Criar UsuarioSistema para usuários órfãos ou desativá-los")
    else:
        print("✅ NENHUM PROBLEMA DE SEGURANÇA ENCONTRADO!")
    
    return len(problemas) == 0

def corrigir_problemas_seguranca():
    """Corrige automaticamente problemas de segurança"""
    print("\n🔧 CORRIGINDO PROBLEMAS DE SEGURANÇA...")
    
    # 1. Remover privilégios de superuser de usuários de loja
    usuarios_loja_superuser = UsuarioSistema.objects.filter(
        user__is_superuser=True,
        is_active=True
    ).exclude(
        user__username__in=['superadmin', 'admin']  # Proteger superadmins legítimos
    )
    
    for usuario in usuarios_loja_superuser:
        print(f"   🔒 Removendo privilégios de superuser de: {usuario.user.username}")
        usuario.user.is_superuser = False
        usuario.user.is_staff = False
        usuario.user.save()
    
    print(f"✅ Corrigidos {usuarios_loja_superuser.count()} usuários com privilégios incorretos")

if __name__ == "__main__":
    print("Executando auditoria...")
    seguro = auditoria_seguranca()
    
    if not seguro:
        resposta = input("\n❓ Deseja corrigir os problemas automaticamente? (s/N): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            corrigir_problemas_seguranca()
            print("\n🔄 Executando nova auditoria...")
            auditoria_seguranca()
    
    print("\n✅ Auditoria concluída!")