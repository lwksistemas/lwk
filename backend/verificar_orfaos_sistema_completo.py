#!/usr/bin/env python
"""
Script para verificar dados órfãos no sistema após exclusão de múltiplas lojas
Verifica: schemas PostgreSQL, usuários, arquivos, Asaas, etc.
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
from superadmin.models import Loja

print("=" * 80)
print("🔍 VERIFICAÇÃO COMPLETA DE DADOS ÓRFÃOS NO SISTEMA")
print("=" * 80)

# 1. LISTAR LOJAS ATIVAS
print("\n1️⃣ LOJAS ATIVAS NO SISTEMA")
print("-" * 80)
lojas_ativas = Loja.objects.all()
print(f"Total de lojas ativas: {lojas_ativas.count()}")
if lojas_ativas.exists():
    print("\nLojas encontradas:")
    for loja in lojas_ativas:
        print(f"   - ID: {loja.id:3d} | Slug: {loja.slug:20s} | Nome: {loja.nome}")
else:
    print("   Nenhuma loja ativa no sistema")

# 2. VERIFICAR SCHEMAS POSTGRESQL ÓRFÃOS
print("\n2️⃣ VERIFICANDO SCHEMAS POSTGRESQL ÓRFÃOS")
print("-" * 80)
try:
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if 'postgres' in DATABASE_URL.lower():
        # Buscar todos os schemas que começam com 'loja_'
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'loja_%'
                ORDER BY schema_name
            """)
            schemas_db = [row[0] for row in cursor.fetchall()]
        
        print(f"Schemas 'loja_*' encontrados no PostgreSQL: {len(schemas_db)}")
        
        # Schemas esperados (das lojas ativas)
        schemas_esperados = set()
        for loja in lojas_ativas:
            schema_name = loja.database_name.replace('-', '_')
            schemas_esperados.add(schema_name)
        
        # Identificar órfãos
        schemas_orfaos = []
        for schema in schemas_db:
            if schema not in schemas_esperados:
                schemas_orfaos.append(schema)
        
        if schemas_orfaos:
            print(f"\n❌ ERRO: {len(schemas_orfaos)} schema(s) órfão(s) encontrado(s):")
            for schema in schemas_orfaos:
                # Contar tabelas no schema
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, [schema])
                    table_count = cursor.fetchone()[0]
                
                print(f"   - {schema} ({table_count} tabelas)")
                
                # Calcular tamanho do schema
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"""
                            SELECT pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))::bigint)
                            FROM pg_tables
                            WHERE schemaname = %s
                        """, [schema])
                        size = cursor.fetchone()[0]
                        if size:
                            print(f"     Tamanho: {size}")
                except Exception as e:
                    pass
            
            print("\n🔧 COMANDO PARA LIMPAR SCHEMAS ÓRFÃOS:")
            print("   Execute no Heroku PostgreSQL:")
            for schema in schemas_orfaos:
                print(f'   DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
        else:
            print("✅ Nenhum schema órfão encontrado")
            
    else:
        print("ℹ️  Não está usando PostgreSQL (desenvolvimento local)")
except Exception as e:
    print(f"❌ Erro ao verificar schemas: {e}")
    import traceback
    traceback.print_exc()

# 3. VERIFICAR USUÁRIOS ÓRFÃOS
print("\n3️⃣ VERIFICANDO USUÁRIOS ÓRFÃOS")
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
        print(f"❌ ERRO: {users_sem_loja.count()} usuário(s) órfão(s) encontrado(s):")
        for user in users_sem_loja:
            print(f"   - ID: {user.id:4d} | Username: {user.username:20s} | Email: {user.email}")
            print(f"     Criado em: {user.date_joined.strftime('%d/%m/%Y %H:%M')}")
            
            # Verificar se tem profissionais/vendedores vinculados
            from superadmin.models import ProfissionalUsuario, VendedorUsuario
            prof_count = ProfissionalUsuario.objects.filter(user=user).count()
            vend_count = VendedorUsuario.objects.filter(user=user).count()
            if prof_count > 0 or vend_count > 0:
                print(f"     ⚠️  Tem vínculos: {prof_count} profissional(is), {vend_count} vendedor(es)")
        
        print("\n🔧 COMANDO PARA LIMPAR USUÁRIOS ÓRFÃOS:")
        print("   Execute no Django shell:")
        print("   from django.contrib.auth.models import User")
        for user in users_sem_loja:
            print(f"   User.objects.get(id={user.id}).delete()  # {user.username}")
    else:
        print("✅ Nenhum usuário órfão encontrado")
        
except Exception as e:
    print(f"❌ Erro ao verificar usuários: {e}")

# 4. VERIFICAR PROFISSIONAIS/VENDEDORES ÓRFÃOS
print("\n4️⃣ VERIFICANDO PROFISSIONAIS/VENDEDORES ÓRFÃOS")
print("-" * 80)
try:
    from superadmin.models import ProfissionalUsuario, VendedorUsuario
    
    # Profissionais órfãos (loja não existe mais)
    profissionais_orfaos = []
    for prof in ProfissionalUsuario.objects.all():
        try:
            _ = prof.loja  # Tenta acessar a loja
        except Loja.DoesNotExist:
            profissionais_orfaos.append(prof)
    
    if profissionais_orfaos:
        print(f"❌ ERRO: {len(profissionais_orfaos)} profissional(is) órfão(s):")
        for prof in profissionais_orfaos:
            print(f"   - ID: {prof.id} | User: {prof.user.username} | Loja ID: {prof.loja_id}")
    else:
        print("✅ Nenhum profissional órfão")
    
    # Vendedores órfãos
    vendedores_orfaos = []
    for vend in VendedorUsuario.objects.all():
        try:
            _ = vend.loja
        except Loja.DoesNotExist:
            vendedores_orfaos.append(vend)
    
    if vendedores_orfaos:
        print(f"❌ ERRO: {len(vendedores_orfaos)} vendedor(es) órfão(s):")
        for vend in vendedores_orfaos:
            print(f"   - ID: {vend.id} | User: {vend.user.username} | Loja ID: {vend.loja_id}")
    else:
        print("✅ Nenhum vendedor órfão")
        
except Exception as e:
    print(f"❌ Erro ao verificar profissionais/vendedores: {e}")

# 5. VERIFICAR FINANCEIRO/PAGAMENTOS ÓRFÃOS
print("\n5️⃣ VERIFICANDO FINANCEIRO/PAGAMENTOS ÓRFÃOS")
print("-" * 80)
try:
    from superadmin.models import FinanceiroLoja, PagamentoLoja
    
    # Financeiros órfãos
    financeiros_orfaos = []
    for fin in FinanceiroLoja.objects.all():
        try:
            _ = fin.loja
        except Loja.DoesNotExist:
            financeiros_orfaos.append(fin)
    
    if financeiros_orfaos:
        print(f"❌ ERRO: {len(financeiros_orfaos)} financeiro(s) órfão(s):")
        for fin in financeiros_orfaos:
            print(f"   - ID: {fin.id} | Loja ID: {fin.loja_id}")
    else:
        print("✅ Nenhum financeiro órfão")
    
    # Pagamentos órfãos
    pagamentos_orfaos = []
    for pag in PagamentoLoja.objects.all():
        try:
            _ = pag.loja
        except Loja.DoesNotExist:
            pagamentos_orfaos.append(pag)
    
    if pagamentos_orfaos:
        print(f"❌ ERRO: {len(pagamentos_orfaos)} pagamento(s) órfão(s):")
        for pag in pagamentos_orfaos[:10]:  # Mostrar apenas primeiros 10
            print(f"   - ID: {pag.id} | Loja ID: {pag.loja_id} | Valor: R$ {pag.valor}")
        if len(pagamentos_orfaos) > 10:
            print(f"   ... e mais {len(pagamentos_orfaos) - 10} pagamentos")
    else:
        print("✅ Nenhum pagamento órfão")
        
except Exception as e:
    print(f"❌ Erro ao verificar financeiro/pagamentos: {e}")

# 6. VERIFICAR ASAAS INTEGRATION
print("\n6️⃣ VERIFICANDO ASAAS INTEGRATION")
print("-" * 80)
try:
    from asaas_integration.models import LojaAssinatura, AsaasCustomer, AsaasPayment
    
    # Slugs das lojas ativas
    slugs_ativos = set(lojas_ativas.values_list('slug', flat=True))
    
    # LojaAssinatura órfãs
    assinaturas_orfas = []
    for ass in LojaAssinatura.objects.all():
        if ass.loja_slug not in slugs_ativos:
            assinaturas_orfas.append(ass)
    
    if assinaturas_orfas:
        print(f"❌ ERRO: {len(assinaturas_orfas)} assinatura(s) Asaas órfã(s):")
        for ass in assinaturas_orfas:
            print(f"   - ID: {ass.id} | Slug: {ass.loja_slug} | Nome: {ass.loja_nome}")
            print(f"     Customer: {ass.asaas_customer.asaas_id if ass.asaas_customer else 'N/A'}")
    else:
        print("✅ Nenhuma assinatura Asaas órfã")
    
    # AsaasCustomer órfãos (external_reference não corresponde a nenhuma loja ativa)
    customers_orfaos = []
    for cust in AsaasCustomer.objects.all():
        if cust.external_reference:
            # Extrair slug do external_reference (formato: loja_SLUG)
            slug = cust.external_reference.replace('loja_', '')
            if slug not in slugs_ativos:
                customers_orfaos.append(cust)
    
    if customers_orfaos:
        print(f"\n⚠️  {len(customers_orfaos)} cliente(s) Asaas potencialmente órfão(s):")
        for cust in customers_orfaos[:10]:
            print(f"   - ID: {cust.id} | Nome: {cust.name} | Ref: {cust.external_reference}")
        if len(customers_orfaos) > 10:
            print(f"   ... e mais {len(customers_orfaos) - 10} clientes")
    else:
        print("✅ Nenhum cliente Asaas órfão")
    
    # AsaasPayment órfãos
    payments_orfaos = []
    for pay in AsaasPayment.objects.all():
        if pay.external_reference:
            # Extrair slug do external_reference
            parts = pay.external_reference.split('_')
            if len(parts) >= 2:
                slug = parts[1]
                if slug not in slugs_ativos:
                    payments_orfaos.append(pay)
    
    if payments_orfaos:
        print(f"\n⚠️  {len(payments_orfaos)} pagamento(s) Asaas potencialmente órfão(s):")
        for pay in payments_orfaos[:10]:
            print(f"   - ID: {pay.id} | Status: {pay.status} | Valor: R$ {pay.value}")
        if len(payments_orfaos) > 10:
            print(f"   ... e mais {len(payments_orfaos) - 10} pagamentos")
    else:
        print("✅ Nenhum pagamento Asaas órfão")
        
except Exception as e:
    print(f"❌ Erro ao verificar Asaas: {e}")
    import traceback
    traceback.print_exc()

# 7. VERIFICAR DIRETÓRIOS DE BACKUP
print("\n7️⃣ VERIFICANDO DIRETÓRIOS DE BACKUP")
print("-" * 80)
try:
    backups_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
    if os.path.exists(backups_dir):
        # Listar todos os diretórios em backups/
        subdirs = [d for d in os.listdir(backups_dir) if os.path.isdir(os.path.join(backups_dir, d))]
        
        # Slugs das lojas ativas
        slugs_ativos = set(lojas_ativas.values_list('slug', flat=True))
        
        # Identificar diretórios órfãos
        dirs_orfaos = []
        for subdir in subdirs:
            if subdir not in slugs_ativos:
                dir_path = os.path.join(backups_dir, subdir)
                files = os.listdir(dir_path)
                total_size = sum(
                    os.path.getsize(os.path.join(dir_path, f)) 
                    for f in files 
                    if os.path.isfile(os.path.join(dir_path, f))
                )
                dirs_orfaos.append((subdir, len(files), total_size))
        
        if dirs_orfaos:
            print(f"⚠️  {len(dirs_orfaos)} diretório(s) de backup órfão(s):")
            total_size_mb = 0
            for subdir, file_count, size in dirs_orfaos:
                size_mb = size / (1024 * 1024)
                total_size_mb += size_mb
                print(f"   - {subdir}: {file_count} arquivo(s), {size_mb:.2f} MB")
            print(f"\n   Total: {total_size_mb:.2f} MB em backups órfãos")
            
            print("\n🔧 AÇÃO RECOMENDADA:")
            print("   Mover para pasta de arquivamento ou excluir se não forem mais necessários")
        else:
            print("✅ Nenhum diretório de backup órfão")
    else:
        print("ℹ️  Diretório de backups não existe")
except Exception as e:
    print(f"❌ Erro ao verificar backups: {e}")

# 8. VERIFICAR ARQUIVOS MEDIA
print("\n8️⃣ VERIFICANDO ARQUIVOS MEDIA")
print("-" * 80)
try:
    media_dir = os.path.join(os.path.dirname(__file__), '..', 'media')
    if os.path.exists(media_dir):
        import glob
        
        # Buscar arquivos com padrão loja_*
        loja_files = glob.glob(os.path.join(media_dir, '**', 'loja_*'), recursive=True)
        
        if loja_files:
            print(f"⚠️  {len(loja_files)} arquivo(s) com padrão 'loja_*' encontrado(s)")
            
            # Slugs das lojas ativas (normalizado)
            slugs_ativos_normalized = set()
            for slug in lojas_ativas.values_list('slug', flat=True):
                slugs_ativos_normalized.add(slug.replace('-', '_'))
            
            # Identificar arquivos órfãos
            files_orfaos = []
            for file_path in loja_files:
                file_name = os.path.basename(file_path)
                # Extrair slug do nome do arquivo (formato: loja_SLUG_...)
                parts = file_name.split('_')
                if len(parts) >= 2:
                    slug = parts[1]
                    if slug not in slugs_ativos_normalized:
                        size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                        files_orfaos.append((file_name, size))
            
            if files_orfaos:
                print(f"\n⚠️  {len(files_orfaos)} arquivo(s) órfão(s) identificado(s):")
                total_size_mb = 0
                for file_name, size in files_orfaos[:10]:
                    size_mb = size / (1024 * 1024)
                    total_size_mb += size_mb
                    print(f"   - {file_name} ({size_mb:.2f} MB)")
                if len(files_orfaos) > 10:
                    print(f"   ... e mais {len(files_orfaos) - 10} arquivos")
                print(f"\n   Total: {total_size_mb:.2f} MB em arquivos órfãos")
            else:
                print("✅ Todos os arquivos pertencem a lojas ativas")
        else:
            print("✅ Nenhum arquivo com padrão 'loja_*' encontrado")
    else:
        print("ℹ️  Diretório media não existe")
except Exception as e:
    print(f"❌ Erro ao verificar media: {e}")

# 9. VERIFICAR CONFIGURAÇÕES DE BANCO NO SETTINGS
print("\n9️⃣ VERIFICANDO CONFIGURAÇÕES DE BANCO NO SETTINGS")
print("-" * 80)
try:
    from django.conf import settings
    
    # Databases configurados
    db_configs = list(settings.DATABASES.keys())
    db_configs.remove('default')  # Remover default
    
    # Database names das lojas ativas
    db_names_ativos = set(lojas_ativas.values_list('database_name', flat=True))
    
    # Identificar configs órfãos
    configs_orfaos = []
    for db_name in db_configs:
        if db_name.startswith('loja_') and db_name not in db_names_ativos:
            configs_orfaos.append(db_name)
    
    if configs_orfaos:
        print(f"⚠️  {len(configs_orfaos)} configuração(ões) de banco órfã(s) no settings:")
        for db_name in configs_orfaos:
            print(f"   - {db_name}")
        print("\n   ℹ️  Essas configs são temporárias e serão removidas ao reiniciar o servidor")
    else:
        print("✅ Nenhuma configuração de banco órfã no settings")
        
except Exception as e:
    print(f"❌ Erro ao verificar settings: {e}")

# RESUMO FINAL
print("\n" + "=" * 80)
print("📊 RESUMO DA VERIFICAÇÃO")
print("=" * 80)
print(f"""
Lojas ativas no sistema: {lojas_ativas.count()}

LEGENDA:
✅ = OK (sem dados órfãos)
⚠️  = Atenção (verificar manualmente)
❌ = Erro (dados órfãos encontrados - requer limpeza)

PRÓXIMOS PASSOS:
1. Se houver schemas PostgreSQL órfãos: executar DROP SCHEMA no Heroku
2. Se houver usuários órfãos: executar script de limpeza
3. Se houver dados Asaas órfãos: verificar se são legítimos antes de excluir
4. Se houver diretórios de backup órfãos: arquivar ou excluir
5. Se houver arquivos media órfãos: excluir manualmente
6. Verificar Cloudinary manualmente no painel web
""")

print("✅ Verificação completa concluída!")
