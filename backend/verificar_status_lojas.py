#!/usr/bin/env python3
"""
Script para verificar o status atual das lojas no sistema
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import TipoLoja, PlanoAssinatura, Loja, UsuarioSistema

def verificar_status():
    """Verifica o status atual do sistema"""
    print("🔍 Verificando status do sistema...")
    print("=" * 50)
    
    # Verificar usuários
    total_users = User.objects.count()
    print(f"👥 Total de usuários: {total_users}")
    
    if total_users > 0:
        print("   Usuários existentes:")
        for user in User.objects.all()[:10]:
            print(f"   - {user.username} ({user.email}) - Ativo: {user.is_active}")
    
    # Verificar tipos de loja
    total_tipos = TipoLoja.objects.count()
    print(f"\n🏪 Total de tipos de loja: {total_tipos}")
    
    if total_tipos > 0:
        print("   Tipos existentes:")
        for tipo in TipoLoja.objects.all():
            print(f"   - {tipo.nome} - Ativo: {tipo.is_active}")
    
    # Verificar planos
    total_planos = PlanoAssinatura.objects.count()
    print(f"\n💳 Total de planos: {total_planos}")
    
    if total_planos > 0:
        print("   Planos existentes:")
        for plano in PlanoAssinatura.objects.all():
            print(f"   - {plano.nome} - R$ {plano.preco_mensal} - Ativo: {plano.is_active}")
    
    # Verificar lojas
    total_lojas = Loja.objects.count()
    print(f"\n🏬 Total de lojas: {total_lojas}")
    
    if total_lojas > 0:
        print("   Lojas existentes:")
        for loja in Loja.objects.all():
            print(f"   - {loja.nome} ({loja.slug}) - Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'} - Ativo: {loja.is_active}")
    else:
        print("   ❌ NENHUMA LOJA ENCONTRADA!")
    
    # Verificar usuários do sistema
    total_usuarios_sistema = UsuarioSistema.objects.count()
    print(f"\n👤 Total de usuários do sistema: {total_usuarios_sistema}")
    
    if total_usuarios_sistema > 0:
        print("   Usuários do sistema:")
        for usuario in UsuarioSistema.objects.all():
            loja_nome = usuario.loja.nome if usuario.loja else 'SEM LOJA'
            print(f"   - {usuario.user.username} - Loja: {loja_nome} - Ativo: {usuario.is_active}")
    
    # Verificar dados da clínica
    try:
        from clinica_estetica.models import Cliente, Profissional, Procedimento
        
        total_clientes = Cliente.objects.count()
        total_profissionais = Profissional.objects.count()
        total_procedimentos = Procedimento.objects.count()
        
        print(f"\n🏥 Dados da clínica:")
        print(f"   - Clientes: {total_clientes}")
        print(f"   - Profissionais: {total_profissionais}")
        print(f"   - Procedimentos: {total_procedimentos}")
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar dados da clínica: {e}")
    
    print("\n" + "=" * 50)
    
    # Diagnóstico
    if total_lojas == 0:
        print("🚨 PROBLEMA IDENTIFICADO: Não há lojas no sistema!")
        print("💡 Possíveis causas:")
        print("   1. Dados foram excluídos durante migração")
        print("   2. Problema na configuração do banco")
        print("   3. Limpeza acidental de dados")
        print("\n🔧 Solução: Executar script de recriação de dados")
    else:
        print("✅ Sistema parece estar funcionando normalmente")

if __name__ == "__main__":
    verificar_status()