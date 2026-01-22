#!/usr/bin/env python3
"""
Script para verificar se a loja Felix existe e criar se necessário
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import TipoLoja, PlanoAssinatura, Loja, UsuarioSistema

def verificar_e_criar_loja_felix():
    """Verifica se a loja Felix existe e cria se necessário"""
    print("🔍 Verificando loja Felix...")
    
    # 1. Verificar se loja existe
    loja = Loja.objects.filter(slug='felix').first()
    if loja:
        print(f"✅ Loja Felix encontrada: {loja.nome} (ID: {loja.id})")
        print(f"   - Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'}")
        print(f"   - Ativa: {loja.is_active}")
    else:
        print("❌ Loja Felix NÃO encontrada!")
        
        # Criar tipo de loja se não existir
        tipo_clinica, created = TipoLoja.objects.get_or_create(
            nome='Clínica de Estética',
            defaults={
                'descricao': 'Sistema completo para clínicas de estética',
                'cor_primaria': '#8B5CF6',
                'cor_secundaria': '#A78BFA',
                'icone': '🏥',
                'is_active': True
            }
        )
        print(f"{'✅ Criado' if created else '✅ Encontrado'} tipo: {tipo_clinica.nome}")
        
        # Criar plano se não existir
        plano, created = PlanoAssinatura.objects.get_or_create(
            nome='Plano Clínica Básico',
            defaults={
                'descricao': 'Plano básico para clínicas de estética',
                'preco_mensal': 99.90,
                'max_usuarios': 5,
                'max_produtos': 100,
                'recursos_inclusos': ['Agendamentos', 'Evolução', 'Protocolos'],
                'is_active': True
            }
        )
        print(f"{'✅ Criado' if created else '✅ Encontrado'} plano: {plano.nome}")
        
        # Criar loja
        loja = Loja.objects.create(
            nome='Clínica Felix',
            slug='felix',
            descricao='Clínica de estética especializada em tratamentos faciais e corporais',
            tipo_loja=tipo_clinica,
            plano_assinatura=plano,
            endereco='Rua das Flores, 123',
            cidade='São Paulo',
            estado='SP',
            telefone='(11) 99999-9999',
            email='contato@clinicafelix.com.br',
            cor_primaria='#8B5CF6',
            cor_secundaria='#A78BFA',
            is_active=True
        )
        print(f"✅ Loja criada: {loja.nome} (ID: {loja.id})")
    
    # 2. Verificar usuário felipe
    user_felipe = User.objects.filter(username='felipe').first()
    if user_felipe:
        print(f"✅ Usuário felipe encontrado: {user_felipe.email}")
        print(f"   - Ativo: {user_felipe.is_active}")
        print(f"   - Superuser: {user_felipe.is_superuser}")
        print(f"   - Staff: {user_felipe.is_staff}")
        
        # Verificar se tem privilégios incorretos
        if user_felipe.is_superuser:
            print("⚠️  CORRIGINDO: Removendo privilégios de superuser do felipe")
            user_felipe.is_superuser = False
            user_felipe.is_staff = False
            user_felipe.save()
            print("✅ Privilégios corrigidos")
        
    else:
        print("❌ Usuário felipe NÃO encontrado!")
        user_felipe = User.objects.create_user(
            username='felipe',
            email='felipe@clinicafelix.com.br',
            password='g$uR1t@!',
            first_name='Felipe',
            last_name='Silva',
            is_active=True,
            is_superuser=False,
            is_staff=False
        )
        print(f"✅ Usuário criado: {user_felipe.username}")
    
    # 3. Verificar UsuarioSistema
    usuario_sistema = UsuarioSistema.objects.filter(user=user_felipe).first()
    if usuario_sistema:
        print(f"✅ UsuarioSistema encontrado para felipe")
        print(f"   - Loja: {usuario_sistema.loja.nome if usuario_sistema.loja else 'SEM LOJA'}")
        print(f"   - Ativo: {usuario_sistema.is_active}")
        
        # Verificar se está vinculado à loja correta
        if usuario_sistema.loja != loja:
            print("⚠️  CORRIGINDO: Vinculando usuário à loja Felix")
            usuario_sistema.loja = loja
            usuario_sistema.save()
            print("✅ Vinculação corrigida")
            
    else:
        print("❌ UsuarioSistema NÃO encontrado para felipe!")
        usuario_sistema = UsuarioSistema.objects.create(
            user=user_felipe,
            loja=loja,
            cargo='Administrador',
            is_active=True,
            senha_provisoria=False,
            senha_alterada=True
        )
        print(f"✅ UsuarioSistema criado para {user_felipe.username}")
    
    # 4. Testar credenciais
    print(f"\n🧪 Testando credenciais...")
    from django.contrib.auth import authenticate
    
    user_test = authenticate(username='felipe', password='g$uR1t@!')
    if user_test:
        print("✅ Credenciais funcionando!")
        print(f"   - Username: {user_test.username}")
        print(f"   - Email: {user_test.email}")
        print(f"   - Ativo: {user_test.is_active}")
    else:
        print("❌ ERRO: Credenciais não funcionam!")
        
        # Tentar resetar senha
        print("🔧 Tentando resetar senha...")
        user_felipe.set_password('g$uR1t@!')
        user_felipe.save()
        
        user_test2 = authenticate(username='felipe', password='g$uR1t@!')
        if user_test2:
            print("✅ Senha resetada com sucesso!")
        else:
            print("❌ ERRO: Ainda não consegue autenticar!")
    
    print(f"\n📋 RESUMO:")
    print(f"   - Loja Felix: {'✅ OK' if loja else '❌ ERRO'}")
    print(f"   - Usuário felipe: {'✅ OK' if user_felipe else '❌ ERRO'}")
    print(f"   - UsuarioSistema: {'✅ OK' if usuario_sistema else '❌ ERRO'}")
    print(f"   - Credenciais: {'✅ OK' if user_test else '❌ ERRO'}")
    
    print(f"\n🔗 URLs para teste:")
    print(f"   - Login: https://lwksistemas.com.br/loja/felix/login")
    print(f"   - Dashboard: https://lwksistemas.com.br/loja/felix/dashboard")
    print(f"   - Credenciais: felipe / g$uR1t@!")

if __name__ == "__main__":
    verificar_e_criar_loja_felix()