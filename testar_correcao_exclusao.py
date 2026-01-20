#!/usr/bin/env python3
"""
Script para testar a correção da exclusão de lojas
Verifica se usuários órfãos são removidos corretamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('backend')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
import random
import string

def gerar_dados_teste():
    """Gera dados únicos para teste"""
    timestamp = str(random.randint(1000, 9999))
    return {
        'nome': f'Loja Teste Exclusão {timestamp}',
        'slug': f'loja-teste-exclusao-{timestamp}',
        'username': f'teste_exclusao_{timestamp}',
        'email': f'teste.exclusao.{timestamp}@lwksistemas.com.br',
        'cpf_cnpj': f'{random.randint(10000000000, 99999999999)}'
    }

def main():
    print("🧪 TESTE DE CORREÇÃO DA EXCLUSÃO DE LOJAS")
    print("=" * 50)
    
    # 1. Estado inicial
    print("\n1️⃣ Estado inicial do sistema:")
    usuarios_inicial = User.objects.count()
    lojas_inicial = Loja.objects.count()
    print(f"   Usuários: {usuarios_inicial}")
    print(f"   Lojas: {lojas_inicial}")
    
    # Listar usuários atuais
    print("\n   Usuários existentes:")
    for user in User.objects.all():
        print(f"   - {user.username} ({user.email}) - Staff: {user.is_staff}, Super: {user.is_superuser}")
    
    # 2. Buscar plano e tipo para teste
    try:
        plano = PlanoAssinatura.objects.filter(is_active=True).first()
        tipo_loja = TipoLoja.objects.first()
        
        if not plano or not tipo_loja:
            print("❌ Erro: Plano ou tipo de loja não encontrado")
            return
        
        print(f"\n   Usando plano: {plano.nome}")
        print(f"   Usando tipo: {tipo_loja.nome}")
        
    except Exception as e:
        print(f"❌ Erro ao buscar plano/tipo: {e}")
        return
    
    # 3. Criar loja de teste
    print("\n2️⃣ Criando loja de teste...")
    dados = gerar_dados_teste()
    
    try:
        # Criar usuário
        owner = User.objects.create_user(
            username=dados['username'],
            email=dados['email'],
            password='senha123',
            is_staff=False  # CORREÇÃO: Não marcar como staff
        )
        print(f"   ✅ Usuário criado: {owner.username} (Staff: {owner.is_staff})")
        
        # Criar loja
        loja = Loja.objects.create(
            nome=dados['nome'],
            slug=dados['slug'],
            cpf_cnpj=dados['cpf_cnpj'],
            tipo_loja=tipo_loja,
            plano=plano,
            owner=owner
        )
        print(f"   ✅ Loja criada: {loja.nome} (ID: {loja.id})")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar loja: {e}")
        return
    
    # 4. Verificar estado após criação
    print("\n3️⃣ Estado após criação:")
    usuarios_apos_criar = User.objects.count()
    lojas_apos_criar = Loja.objects.count()
    print(f"   Usuários: {usuarios_apos_criar} (+{usuarios_apos_criar - usuarios_inicial})")
    print(f"   Lojas: {lojas_apos_criar} (+{lojas_apos_criar - lojas_inicial})")
    
    # 5. Excluir a loja
    print("\n4️⃣ Excluindo a loja...")
    try:
        loja_id = loja.id
        loja_nome = loja.nome
        owner_username = owner.username
        
        # Excluir usando o método do modelo (isso deve acionar os signals)
        loja.delete()
        print(f"   ✅ Loja excluída: {loja_nome} (ID: {loja_id})")
        
    except Exception as e:
        print(f"   ❌ Erro ao excluir loja: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Verificar estado após exclusão
    print("\n5️⃣ Estado após exclusão:")
    usuarios_apos_excluir = User.objects.count()
    lojas_apos_excluir = Loja.objects.count()
    print(f"   Usuários: {usuarios_apos_excluir} ({usuarios_apos_excluir - usuarios_apos_criar:+d})")
    print(f"   Lojas: {lojas_apos_excluir} ({lojas_apos_excluir - lojas_apos_criar:+d})")
    
    # Verificar se o usuário foi removido
    try:
        user_ainda_existe = User.objects.filter(username=owner_username).exists()
        if user_ainda_existe:
            print(f"   ❌ PROBLEMA: Usuário {owner_username} ainda existe!")
            user = User.objects.get(username=owner_username)
            print(f"      - Staff: {user.is_staff}, Super: {user.is_superuser}")
        else:
            print(f"   ✅ Usuário {owner_username} foi removido corretamente")
    except Exception as e:
        print(f"   ❌ Erro ao verificar usuário: {e}")
    
    # 7. Testar criação com mesmo email
    print("\n6️⃣ Testando criação com mesmo email...")
    try:
        # Tentar criar usuário com mesmo email
        novo_owner = User.objects.create_user(
            username=dados['username'] + '_novo',
            email=dados['email'],  # Mesmo email
            password='senha123',
            is_staff=False
        )
        
        # Tentar criar loja com mesmo slug
        nova_loja = Loja.objects.create(
            nome=dados['nome'] + ' Nova',
            slug=dados['slug'] + '-nova',
            cpf_cnpj=dados['cpf_cnpj'],
            tipo_loja=tipo_loja,
            plano=plano,
            owner=novo_owner
        )
        
        print(f"   ✅ Nova loja criada com sucesso: {nova_loja.nome}")
        
        # Limpar teste
        nova_loja.delete()
        print(f"   🧹 Loja de teste removida")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar nova loja: {e}")
    
    # 8. Resultado final
    print("\n🎯 RESULTADO DO TESTE:")
    usuarios_final = User.objects.count()
    lojas_final = Loja.objects.count()
    
    if usuarios_final == usuarios_inicial and lojas_final == lojas_inicial:
        print("   ✅ SUCESSO: Sistema voltou ao estado inicial")
        print("   ✅ Usuário órfão foi removido corretamente")
        print("   ✅ Correção funcionando!")
    else:
        print("   ❌ PROBLEMA: Sistema não voltou ao estado inicial")
        print(f"   ❌ Usuários: {usuarios_inicial} → {usuarios_final}")
        print(f"   ❌ Lojas: {lojas_inicial} → {lojas_final}")
    
    print("\n   Usuários finais:")
    for user in User.objects.all():
        print(f"   - {user.username} ({user.email}) - Staff: {user.is_staff}, Super: {user.is_superuser}")

if __name__ == '__main__':
    main()