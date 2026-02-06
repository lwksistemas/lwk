#!/usr/bin/env python
"""
Script para criar uma loja de teste do tipo Cabeleireiro
e verificar se o admin é vinculado automaticamente como funcionário.

Execute: python backend/criar_loja_teste_cabeleireiro.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from superadmin.models import Loja, TipoLoja, PlanoAssinatura
from cabeleireiro.models import Funcionario
from datetime import datetime, timedelta
import random
import string

def gerar_senha_provisoria(tamanho=8):
    """Gera senha provisória aleatória"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

def criar_loja_teste():
    """Cria loja de teste do tipo Cabeleireiro"""
    
    print("\n" + "="*60)
    print("🧪 CRIANDO LOJA DE TESTE - CABELEIREIRO")
    print("="*60 + "\n")
    
    # 1. Verificar se tipo Cabeleireiro existe
    print("1️⃣ Verificando tipo de loja 'Cabeleireiro'...")
    try:
        tipo_cabeleireiro = TipoLoja.objects.get(slug='cabeleireiro')
        print(f"   ✅ Tipo encontrado: {tipo_cabeleireiro.nome}")
    except TipoLoja.DoesNotExist:
        print("   ❌ Tipo 'Cabeleireiro' não encontrado!")
        print("   Execute: python manage.py shell < scripts/criar_tipo_loja_cabeleireiro.py")
        return
    
    # 2. Verificar se existe plano
    print("\n2️⃣ Verificando plano de assinatura...")
    plano = PlanoAssinatura.objects.filter(is_active=True).first()
    if not plano:
        print("   ❌ Nenhum plano ativo encontrado!")
        return
    print(f"   ✅ Plano encontrado: {plano.nome}")
    
    # 3. Criar ou obter usuário de teste
    print("\n3️⃣ Criando usuário de teste...")
    username = f"teste_cabeleireiro_{random.randint(1000, 9999)}"
    email = f"{username}@teste.com"
    senha_provisoria = gerar_senha_provisoria()
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha_provisoria,
            first_name="Teste",
            last_name="Cabeleireiro"
        )
        print(f"   ✅ Usuário criado: {user.username}")
        print(f"   📧 Email: {email}")
        print(f"   🔑 Senha: {senha_provisoria}")
    except Exception as e:
        print(f"   ❌ Erro ao criar usuário: {e}")
        return
    
    # 4. Criar loja
    print("\n4️⃣ Criando loja de teste...")
    nome_loja = f"Salão Teste {random.randint(1000, 9999)}"
    
    try:
        loja = Loja.objects.create(
            nome=nome_loja,
            descricao="Loja de teste para verificar vinculação automática do admin como funcionário",
            tipo_loja=tipo_cabeleireiro,
            plano=plano,
            owner=user,
            senha_provisoria=senha_provisoria,
            is_active=True,
            is_trial=True,
            trial_ends_at=datetime.now() + timedelta(days=30),
            cpf_cnpj="12345678901234"  # CNPJ fictício
        )
        print(f"   ✅ Loja criada: {loja.nome}")
        print(f"   🔗 Slug: {loja.slug}")
        print(f"   🆔 ID: {loja.id}")
        print(f"   🌐 URL: https://lwksistemas.com.br/loja/{loja.slug}/dashboard")
    except Exception as e:
        print(f"   ❌ Erro ao criar loja: {e}")
        user.delete()  # Limpar usuário criado
        return
    
    # 5. Verificar se funcionário foi criado automaticamente (signal)
    print("\n5️⃣ Verificando vinculação automática do admin como funcionário...")
    print("   ⏳ Aguardando signal processar...")
    
    import time
    time.sleep(2)  # Aguardar signal processar
    
    try:
        # Buscar funcionário criado pelo signal
        funcionario = Funcionario.objects.filter(
            loja_id=loja.id,
            email=user.email
        ).first()
        
        if funcionario:
            print(f"   ✅ SUCESSO! Funcionário criado automaticamente:")
            print(f"      👤 Nome: {funcionario.nome}")
            print(f"      📧 Email: {funcionario.email}")
            print(f"      💼 Cargo: {funcionario.cargo}")
            print(f"      🔧 Função: {funcionario.funcao}")
            print(f"      📅 Data Admissão: {funcionario.data_admissao}")
            print(f"      ✅ Ativo: {funcionario.is_active}")
            print(f"      🔒 É Admin: {funcionario.is_admin if hasattr(funcionario, 'is_admin') else 'N/A'}")
        else:
            print(f"   ❌ FALHA! Funcionário NÃO foi criado automaticamente")
            print(f"   🔍 Verificando se signal está configurado...")
            
            # Verificar se signal está registrado
            from django.db.models.signals import post_save
            from cabeleireiro.signals import criar_funcionario_admin_automaticamente
            
            receivers = post_save._live_receivers(Loja)
            signal_registrado = any(
                receiver.__name__ == 'criar_funcionario_admin_automaticamente' 
                for receiver in receivers
            )
            
            if signal_registrado:
                print(f"   ✅ Signal está registrado")
                print(f"   ⚠️ Mas não foi executado. Possíveis causas:")
                print(f"      - Tipo da loja não é 'Cabeleireiro'")
                print(f"      - Erro na execução do signal")
            else:
                print(f"   ❌ Signal NÃO está registrado!")
                print(f"   📝 Verifique: backend/cabeleireiro/apps.py")
    
    except Exception as e:
        print(f"   ❌ Erro ao verificar funcionário: {e}")
    
    # 6. Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DA LOJA DE TESTE")
    print("="*60)
    print(f"🏪 Loja: {loja.nome}")
    print(f"🔗 Slug: {loja.slug}")
    print(f"🆔 ID: {loja.id}")
    print(f"👤 Owner: {user.username}")
    print(f"📧 Email: {email}")
    print(f"🔑 Senha: {senha_provisoria}")
    print(f"🌐 URL Login: https://lwksistemas.com.br/loja/{loja.slug}/login")
    print(f"🌐 URL Dashboard: https://lwksistemas.com.br/loja/{loja.slug}/dashboard")
    print("="*60 + "\n")
    
    # 7. Instruções
    print("📝 PRÓXIMOS PASSOS:")
    print("1. Acesse o dashboard da loja")
    print("2. Clique em '👥 Funcionários'")
    print("3. Verifique se o admin aparece na lista")
    print("4. Tente editar/excluir (deve estar protegido)")
    print("\n")

if __name__ == '__main__':
    criar_loja_teste()
