#!/usr/bin/env python3
"""
Teste completo da correção de exclusão de lojas
Verifica se usuários órfãos são removidos automaticamente
"""
import os
import sys
import django

# Configurar Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
import secrets
import string

def criar_loja_teste():
    """Cria uma loja de teste"""
    print("🏪 Criando loja de teste...")
    
    # Buscar primeiro plano e tipo
    plano = PlanoAssinatura.objects.first()
    tipo = TipoLoja.objects.first()
    
    if not plano or not tipo:
        print("❌ Planos ou tipos de loja não encontrados")
        return None
    
    # Gerar dados únicos
    timestamp = str(int(time.time()))
    username = f"teste_correcao_{timestamp}"
    email = f"teste.correcao.{timestamp}@lwksistemas.com.br"
    
    # Criar usuário
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_staff=True
    )
    
    # Criar loja
    loja = Loja.objects.create(
        nome=f"Loja Teste Correção {timestamp}",
        slug=f"loja-teste-correcao-{timestamp}",
        cpf_cnpj="12345678901",
        tipo_loja=tipo,
        plano=plano,
        tipo_assinatura="mensal",
        owner=user,
        senha_provisoria=password
    )
    
    print(f"✅ Loja criada: {loja.nome}")
    print(f"   ID: {loja.id}")
    print(f"   Owner: {user.username} ({user.email})")
    
    return loja, user

def main():
    """Função principal"""
    import time
    
    print("🧪 TESTE COMPLETO DA CORREÇÃO DE EXCLUSÃO")
    print("=" * 50)
    
    # 1. Estado inicial
    print("📊 Estado inicial:")
    usuarios_inicial = User.objects.count()
    lojas_inicial = Loja.objects.count()
    print(f"   Usuários: {usuarios_inicial}")
    print(f"   Lojas: {lojas_inicial}")
    
    # 2. Criar loja de teste
    loja, user = criar_loja_teste()
    if not loja:
        return
    
    # 3. Verificar estado após criação
    print("\n📊 Estado após criação:")
    usuarios_apos_criacao = User.objects.count()
    lojas_apos_criacao = Loja.objects.count()
    print(f"   Usuários: {usuarios_apos_criacao}")
    print(f"   Lojas: {lojas_apos_criacao}")
    
    # 4. Excluir a loja (isso deve acionar os signals)
    print(f"\n🗑️  Excluindo loja: {loja.nome}")
    username_para_verificar = user.username
    loja.delete()  # Isso deve acionar os signals de limpeza
    
    # 5. Verificar estado após exclusão
    print("\n📊 Estado após exclusão:")
    usuarios_apos_exclusao = User.objects.count()
    lojas_apos_exclusao = Loja.objects.count()
    print(f"   Usuários: {usuarios_apos_exclusao}")
    print(f"   Lojas: {lojas_apos_exclusao}")
    
    # 6. Verificar se o usuário foi removido
    try:
        User.objects.get(username=username_para_verificar)
        print(f"❌ FALHA: Usuário {username_para_verificar} ainda existe!")
        resultado = "FALHOU"
    except User.DoesNotExist:
        print(f"✅ SUCESSO: Usuário {username_para_verificar} foi removido!")
        resultado = "PASSOU"
    
    # 7. Verificar contadores
    usuarios_esperados = usuarios_inicial
    lojas_esperadas = lojas_inicial
    
    usuarios_ok = usuarios_apos_exclusao == usuarios_esperados
    lojas_ok = lojas_apos_exclusao == lojas_esperadas
    
    print(f"\n📈 Verificação de contadores:")
    print(f"   Usuários: {usuarios_apos_exclusao} == {usuarios_esperados} ({'✅' if usuarios_ok else '❌'})")
    print(f"   Lojas: {lojas_apos_exclusao} == {lojas_esperadas} ({'✅' if lojas_ok else '❌'})")
    
    # 8. Resultado final
    print("\n" + "=" * 50)
    if resultado == "PASSOU" and usuarios_ok and lojas_ok:
        print("🎉 TESTE PASSOU! CORREÇÃO FUNCIONANDO PERFEITAMENTE!")
        print("✅ Usuários órfãos são removidos automaticamente")
        print("✅ Limpeza completa dos dados relacionados")
        print("✅ Contadores corretos após exclusão")
    else:
        print("❌ TESTE FALHOU! CORREÇÃO NÃO ESTÁ FUNCIONANDO")
        if resultado == "FALHOU":
            print("❌ Usuário órfão não foi removido")
        if not usuarios_ok:
            print("❌ Contador de usuários incorreto")
        if not lojas_ok:
            print("❌ Contador de lojas incorreto")
    
    print("\n🎯 PRÓXIMO PASSO: Testar criação de nova loja com mesmo email")

if __name__ == "__main__":
    main()