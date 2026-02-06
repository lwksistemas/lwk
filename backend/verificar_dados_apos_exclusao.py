#!/usr/bin/env python
"""
Script para verificar se todos os dados foram excluídos após exclusão de lojas.
Verifica dados órfãos em todos os apps.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django sem dependências extras
import warnings
warnings.filterwarnings('ignore')

try:
    django.setup()
except Exception as e:
    print(f"Erro ao configurar Django: {e}")
    sys.exit(1)

from django.contrib.auth.models import User
from superadmin.models import Loja, TipoLoja, PlanoAssinatura

print("\n" + "="*70)
print("🔍 VERIFICAÇÃO DE DADOS APÓS EXCLUSÃO DE LOJAS")
print("="*70 + "\n")

# 1. Verificar lojas
print("1️⃣ VERIFICANDO LOJAS...")
lojas = Loja.objects.all()
print(f"   📊 Total de lojas: {lojas.count()}")
if lojas.exists():
    print("   ⚠️ Ainda existem lojas no sistema:")
    for loja in lojas:
        print(f"      - {loja.nome} (ID: {loja.id}, Slug: {loja.slug})")
else:
    print("   ✅ Nenhuma loja encontrada")

# 2. Verificar usuários (owners)
print("\n2️⃣ VERIFICANDO USUÁRIOS...")
users = User.objects.all()
superusers = User.objects.filter(is_superuser=True)
regular_users = User.objects.filter(is_superuser=False)

print(f"   📊 Total de usuários: {users.count()}")
print(f"   👑 Superusuários: {superusers.count()}")
print(f"   👤 Usuários regulares: {regular_users.count()}")

if regular_users.exists():
    print("   ⚠️ Usuários regulares encontrados:")
    for user in regular_users:
        lojas_owned = Loja.objects.filter(owner=user).count()
        print(f"      - {user.username} ({user.email}) - Lojas: {lojas_owned}")
        if lojas_owned == 0:
            print(f"        ⚠️ Usuário órfão (sem lojas)")

# 3. Verificar dados de apps específicos
apps_para_verificar = [
    ('cabeleireiro', ['Cliente', 'Profissional', 'Servico', 'Agendamento', 
                      'Produto', 'Venda', 'Funcionario', 'HorarioFuncionamento', 'BloqueioAgenda']),
    ('clinica_estetica', ['Paciente', 'Profissional', 'Procedimento', 'Consulta', 
                          'Funcionario', 'HorarioFuncionamento']),
    ('crm_vendas', ['Cliente', 'Lead', 'Oportunidade', 'Funcionario']),
    ('servicos', ['Cliente', 'Servico', 'OrdemServico', 'Funcionario']),
    ('restaurante', ['Mesa', 'Produto', 'Pedido', 'Funcionario']),
]

print("\n3️⃣ VERIFICANDO DADOS DOS APPS...")

for app_name, models in apps_para_verificar:
    print(f"\n   📦 App: {app_name}")
    try:
        app_module = __import__(f'{app_name}.models', fromlist=models)
        
        for model_name in models:
            try:
                model_class = getattr(app_module, model_name)
                count = model_class.objects.all().count()
                
                if count > 0:
                    print(f"      ⚠️ {model_name}: {count} registros")
                    
                    # Verificar se tem loja_id
                    if hasattr(model_class, 'loja_id'):
                        # Verificar registros órfãos
                        orfaos = model_class.objects.exclude(
                            loja_id__in=Loja.objects.values_list('id', flat=True)
                        ).count()
                        if orfaos > 0:
                            print(f"         🚨 {orfaos} registros ÓRFÃOS (loja não existe)")
                else:
                    print(f"      ✅ {model_name}: 0 registros")
                    
            except AttributeError:
                print(f"      ⚠️ {model_name}: Modelo não encontrado")
            except Exception as e:
                print(f"      ❌ {model_name}: Erro ao verificar - {e}")
                
    except ImportError:
        print(f"      ⚠️ App não encontrado ou não instalado")
    except Exception as e:
        print(f"      ❌ Erro ao verificar app: {e}")

# 4. Verificar sessões
print("\n4️⃣ VERIFICANDO SESSÕES...")
try:
    from superadmin.models import UserSession
    sessoes = UserSession.objects.all()
    print(f"   📊 Total de sessões: {sessoes.count()}")
    
    if sessoes.exists():
        print("   ⚠️ Sessões ativas encontradas:")
        for sessao in sessoes:
            print(f"      - {sessao.user.username} (Criada: {sessao.created_at})")
except Exception as e:
    print(f"   ❌ Erro ao verificar sessões: {e}")

# 5. Resumo e recomendações
print("\n" + "="*70)
print("📊 RESUMO E RECOMENDAÇÕES")
print("="*70)

total_lojas = Loja.objects.count()
total_users_regulares = User.objects.filter(is_superuser=False).count()

if total_lojas == 0:
    print("✅ Todas as lojas foram excluídas com sucesso")
else:
    print(f"⚠️ Ainda existem {total_lojas} loja(s) no sistema")

if total_users_regulares > 0:
    users_orfaos = 0
    for user in User.objects.filter(is_superuser=False):
        if Loja.objects.filter(owner=user).count() == 0:
            users_orfaos += 1
    
    if users_orfaos > 0:
        print(f"\n⚠️ {users_orfaos} usuário(s) órfão(s) encontrado(s)")
        print("   Recomendação: Excluir usuários órfãos")
        print("   Comando: python manage.py shell")
        print("   >>> from django.contrib.auth.models import User")
        print("   >>> User.objects.filter(is_superuser=False, lojas_owned__isnull=True).delete()")

# Verificar dados órfãos em apps
print("\n🔍 VERIFICANDO DADOS ÓRFÃOS...")
dados_orfaos_encontrados = False

for app_name, models in apps_para_verificar:
    try:
        app_module = __import__(f'{app_name}.models', fromlist=models)
        
        for model_name in models:
            try:
                model_class = getattr(app_module, model_name)
                
                if hasattr(model_class, 'loja_id'):
                    orfaos = model_class.objects.exclude(
                        loja_id__in=Loja.objects.values_list('id', flat=True)
                    ).count()
                    
                    if orfaos > 0:
                        if not dados_orfaos_encontrados:
                            print("\n⚠️ DADOS ÓRFÃOS ENCONTRADOS:")
                            dados_orfaos_encontrados = True
                        print(f"   - {app_name}.{model_name}: {orfaos} registros")
            except:
                pass
    except:
        pass

if dados_orfaos_encontrados:
    print("\n   Recomendação: Executar script de limpeza")
    print("   Script: backend/limpar_dados_orfaos.py")
else:
    print("✅ Nenhum dado órfão encontrado")

print("\n" + "="*70 + "\n")
