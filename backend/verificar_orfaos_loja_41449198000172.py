#!/usr/bin/env python
"""
Script para verificar se ficaram dados órfãos após exclusão da loja 41449198000172
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from superadmin.models import (
    Loja, FinanceiroLoja, PagamentoLoja, 
    ProfissionalUsuario, VendedorUsuario, UsuarioSistema
)

LOJA_SLUG = '41449198000172'
LOJA_CNPJ = '41.449.198/0001-72'

print("=" * 80)
print(f"🔍 VERIFICAÇÃO DE DADOS ÓRFÃOS - Loja {LOJA_SLUG}")
print("=" * 80)

# 1. VERIFICAR SE LOJA EXISTE NO BANCO
print("\n1️⃣ VERIFICANDO LOJA NO BANCO DE DADOS")
print("-" * 80)
try:
    loja = Loja.objects.get(slug=LOJA_SLUG)
    print(f"❌ ERRO: Loja ainda existe no banco!")
    print(f"   ID: {loja.id}")
    print(f"   Nome: {loja.nome}")
    print(f"   Owner: {loja.owner.username}")
    print(f"   Database: {loja.database_name}")
except Loja.DoesNotExist:
    print(f"✅ Loja {LOJA_SLUG} não existe no banco (correto)")

# 2. VERIFICAR FINANCEIRO ÓRFÃO
print("\n2️⃣ VERIFICANDO FINANCEIRO ÓRFÃO")
print("-" * 80)
try:
    financeiros = FinanceiroLoja.objects.filter(loja__slug=LOJA_SLUG)
    if financeiros.exists():
        print(f"❌ ERRO: {financeiros.count()} financeiro(s) órfão(s) encontrado(s)")
        for fin in financeiros:
            print(f"   ID: {fin.id}, Loja ID: {fin.loja_id}")
    else:
        print("✅ Nenhum financeiro órfão encontrado")
except Exception as e:
    print(f"✅ Nenhum financeiro órfão (tabela vazia ou erro: {e})")

# 3. VERIFICAR PAGAMENTOS ÓRFÃOS
print("\n3️⃣ VERIFICANDO PAGAMENTOS ÓRFÃOS")
print("-" * 80)
try:
    pagamentos = PagamentoLoja.objects.filter(loja__slug=LOJA_SLUG)
    if pagamentos.exists():
        print(f"❌ ERRO: {pagamentos.count()} pagamento(s) órfão(s) encontrado(s)")
        for pag in pagamentos:
            print(f"   ID: {pag.id}, Loja ID: {pag.loja_id}, Valor: R$ {pag.valor}")
    else:
        print("✅ Nenhum pagamento órfão encontrado")
except Exception as e:
    print(f"✅ Nenhum pagamento órfão (tabela vazia ou erro: {e})")

# 4. VERIFICAR PROFISSIONAIS/VENDEDORES ÓRFÃOS
print("\n4️⃣ VERIFICANDO PROFISSIONAIS/VENDEDORES ÓRFÃOS")
print("-" * 80)
try:
    profissionais = ProfissionalUsuario.objects.filter(loja__slug=LOJA_SLUG)
    if profissionais.exists():
        print(f"❌ ERRO: {profissionais.count()} profissional(is) órfão(s) encontrado(s)")
        for prof in profissionais:
            print(f"   ID: {prof.id}, User: {prof.user.username}, Loja ID: {prof.loja_id}")
    else:
        print("✅ Nenhum profissional órfão encontrado")
except Exception as e:
    print(f"✅ Nenhum profissional órfão (erro: {e})")

try:
    vendedores = VendedorUsuario.objects.filter(loja__slug=LOJA_SLUG)
    if vendedores.exists():
        print(f"❌ ERRO: {vendedores.count()} vendedor(es) órfão(s) encontrado(s)")
        for vend in vendedores:
            print(f"   ID: {vend.id}, User: {vend.user.username}, Loja ID: {vend.loja_id}")
    else:
        print("✅ Nenhum vendedor órfão encontrado")
except Exception as e:
    print(f"✅ Nenhum vendedor órfão (erro: {e})")

# 5. VERIFICAR SCHEMA POSTGRESQL
print("\n5️⃣ VERIFICANDO SCHEMA POSTGRESQL")
print("-" * 80)
try:
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if 'postgres' in DATABASE_URL.lower():
        schema_name = f"loja_{LOJA_SLUG.replace('-', '_')}"
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                [schema_name]
            )
            schema_exists = cursor.fetchone()
            
            if schema_exists:
                print(f"❌ ERRO: Schema órfão encontrado: {schema_name}")
                
                # Contar tabelas no schema
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                """, [schema_name])
                table_count = cursor.fetchone()[0]
                print(f"   Tabelas no schema: {table_count}")
                
                # Listar tabelas
                if table_count > 0:
                    cursor.execute(f"""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        ORDER BY table_name
                    """, [schema_name])
                    tables = cursor.fetchall()
                    print(f"   Tabelas:")
                    for table in tables[:10]:  # Mostrar apenas primeiras 10
                        print(f"      - {table[0]}")
                    if table_count > 10:
                        print(f"      ... e mais {table_count - 10} tabelas")
            else:
                print(f"✅ Schema {schema_name} não existe (correto)")
    else:
        print("ℹ️  Não está usando PostgreSQL (desenvolvimento local)")
except Exception as e:
    print(f"⚠️  Erro ao verificar schema: {e}")

# 6. VERIFICAR ASAAS INTEGRATION
print("\n6️⃣ VERIFICANDO ASAAS INTEGRATION")
print("-" * 80)
try:
    from asaas_integration.models import LojaAssinatura, AsaasCustomer, AsaasPayment
    
    # LojaAssinatura
    assinaturas = LojaAssinatura.objects.filter(loja_slug=LOJA_SLUG)
    if assinaturas.exists():
        print(f"❌ ERRO: {assinaturas.count()} assinatura(s) Asaas órfã(s)")
        for ass in assinaturas:
            print(f"   ID: {ass.id}, Loja: {ass.loja_nome}, Customer: {ass.asaas_customer_id}")
    else:
        print("✅ Nenhuma assinatura Asaas órfã")
    
    # AsaasCustomer (buscar por external_reference)
    customers = AsaasCustomer.objects.filter(external_reference__contains=LOJA_SLUG)
    if customers.exists():
        print(f"⚠️  {customers.count()} cliente(s) Asaas encontrado(s) (podem ser legítimos)")
        for cust in customers:
            print(f"   ID: {cust.id}, Nome: {cust.name}, Asaas ID: {cust.asaas_id}")
    else:
        print("✅ Nenhum cliente Asaas com referência à loja")
    
    # AsaasPayment (buscar por external_reference)
    payments = AsaasPayment.objects.filter(external_reference__contains=LOJA_SLUG)
    if payments.exists():
        print(f"⚠️  {payments.count()} pagamento(s) Asaas encontrado(s) (podem ser legítimos)")
        for pay in payments[:5]:  # Mostrar apenas primeiros 5
            print(f"   ID: {pay.id}, Status: {pay.status}, Valor: R$ {pay.value}")
    else:
        print("✅ Nenhum pagamento Asaas com referência à loja")
        
except Exception as e:
    print(f"⚠️  Erro ao verificar Asaas: {e}")

# 7. VERIFICAR USUÁRIO OWNER ÓRFÃO
print("\n7️⃣ VERIFICANDO USUÁRIO OWNER ÓRFÃO")
print("-" * 80)
try:
    # Buscar usuários que não são superadmin/staff e não têm lojas
    users_sem_loja = User.objects.filter(
        is_superuser=False,
        is_staff=False,
        lojas_owned__isnull=True
    ).exclude(
        perfil_sistema__isnull=False  # Excluir usuários do sistema
    )
    
    if users_sem_loja.exists():
        print(f"⚠️  {users_sem_loja.count()} usuário(s) sem loja encontrado(s)")
        for user in users_sem_loja:
            print(f"   ID: {user.id}, Username: {user.username}, Email: {user.email}")
            print(f"      Criado em: {user.date_joined}")
    else:
        print("✅ Nenhum usuário órfão encontrado")
        
except Exception as e:
    print(f"⚠️  Erro ao verificar usuários: {e}")

# 8. VERIFICAR ARQUIVOS DE BACKUP
print("\n8️⃣ VERIFICANDO ARQUIVOS DE BACKUP")
print("-" * 80)
backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups', LOJA_SLUG)
if os.path.exists(backup_dir):
    files = os.listdir(backup_dir)
    if files:
        print(f"⚠️  Diretório de backup existe com {len(files)} arquivo(s)")
        print(f"   Caminho: {backup_dir}")
        for file in files[:5]:  # Mostrar apenas primeiros 5
            file_path = os.path.join(backup_dir, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"      - {file} ({size_mb:.2f} MB)")
    else:
        print(f"ℹ️  Diretório de backup existe mas está vazio")
        print(f"   Caminho: {backup_dir}")
else:
    print(f"✅ Diretório de backup não existe (correto)")

# 9. VERIFICAR ARQUIVOS MEDIA
print("\n9️⃣ VERIFICANDO ARQUIVOS MEDIA")
print("-" * 80)
media_dir = os.path.join(os.path.dirname(__file__), '..', 'media')
if os.path.exists(media_dir):
    # Buscar arquivos com referência à loja
    import glob
    loja_files = []
    for pattern in [f'*{LOJA_SLUG}*', f'*loja_{LOJA_SLUG.replace("-", "_")}*']:
        loja_files.extend(glob.glob(os.path.join(media_dir, '**', pattern), recursive=True))
    
    if loja_files:
        print(f"⚠️  {len(loja_files)} arquivo(s) media encontrado(s)")
        for file in loja_files[:5]:  # Mostrar apenas primeiros 5
            size_mb = os.path.getsize(file) / (1024 * 1024)
            print(f"      - {os.path.basename(file)} ({size_mb:.2f} MB)")
    else:
        print(f"✅ Nenhum arquivo media com referência à loja")
else:
    print(f"ℹ️  Diretório media não existe")

# 10. VERIFICAR CLOUDINARY
print("\n🔟 VERIFICANDO CLOUDINARY")
print("-" * 80)
try:
    from superadmin.cloudinary_models import CloudinaryConfig
    config = CloudinaryConfig.get_config()
    
    if config.enabled and config.cloud_name:
        print(f"ℹ️  Cloudinary configurado: {config.cloud_name}")
        print(f"   Pasta da loja: {LOJA_SLUG}/")
        print(f"   ⚠️  Verificação manual necessária no painel do Cloudinary")
        print(f"   URL: https://console.cloudinary.com/console/{config.cloud_name}/media_library/folders/{LOJA_SLUG}")
    else:
        print(f"ℹ️  Cloudinary não configurado")
        
except Exception as e:
    print(f"⚠️  Erro ao verificar Cloudinary: {e}")

# RESUMO FINAL
print("\n" + "=" * 80)
print("📊 RESUMO DA VERIFICAÇÃO")
print("=" * 80)
print("""
✅ = Correto (sem dados órfãos)
⚠️  = Atenção (verificar manualmente)
❌ = Erro (dados órfãos encontrados)

AÇÕES RECOMENDADAS:
1. Se houver schema PostgreSQL órfão: executar DROP SCHEMA manualmente
2. Se houver usuário órfão: executar script de limpeza
3. Se houver arquivos de backup: mover para pasta de arquivamento
4. Se houver arquivos media: excluir manualmente
5. Se houver dados Asaas: verificar se são legítimos antes de excluir
6. Verificar Cloudinary manualmente no painel web
""")

print("\n✅ Verificação concluída!")
