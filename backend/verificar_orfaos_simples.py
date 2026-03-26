#!/usr/bin/env python
"""
Script simples para verificar dados órfãos sem depender do Django completo
Verifica: schemas PostgreSQL, diretórios de backup, arquivos media
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

print("=" * 80)
print("🔍 VERIFICAÇÃO SIMPLES DE DADOS ÓRFÃOS")
print("=" * 80)

# 1. CONECTAR AO POSTGRESQL
print("\n1️⃣ CONECTANDO AO POSTGRESQL")
print("-" * 80)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    print("❌ DATABASE_URL não configurada")
    print("   Configure com: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

# Parse DATABASE_URL
url = urlparse(DATABASE_URL)
conn_params = {
    'host': url.hostname,
    'port': url.port or 5432,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],  # Remove leading /
}

try:
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()
    print(f"✅ Conectado ao PostgreSQL: {conn_params['host']}")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)

# 2. LISTAR LOJAS ATIVAS
print("\n2️⃣ LOJAS ATIVAS NO SISTEMA")
print("-" * 80)
try:
    cursor.execute("SELECT id, slug, nome, database_name FROM superadmin_loja ORDER BY id")
    lojas = cursor.fetchall()
    print(f"Total de lojas ativas: {len(lojas)}")
    
    if lojas:
        print("\nLojas encontradas:")
        for loja_id, slug, nome, db_name in lojas:
            print(f"   - ID: {loja_id:3d} | Slug: {slug:20s} | DB: {db_name}")
    
    # Guardar slugs e database_names para comparação
    slugs_ativos = set(slug for _, slug, _, _ in lojas)
    db_names_ativos = set(db_name for _, _, _, db_name in lojas)
    
except Exception as e:
    print(f"❌ Erro ao listar lojas: {e}")
    slugs_ativos = set()
    db_names_ativos = set()

# 3. VERIFICAR SCHEMAS POSTGRESQL ÓRFÃOS
print("\n3️⃣ VERIFICANDO SCHEMAS POSTGRESQL ÓRFÃOS")
print("-" * 80)
try:
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'loja_%'
        ORDER BY schema_name
    """)
    schemas_db = [row[0] for row in cursor.fetchall()]
    
    print(f"Schemas 'loja_*' encontrados: {len(schemas_db)}")
    
    # Identificar órfãos
    schemas_orfaos = []
    for schema in schemas_db:
        if schema not in db_names_ativos:
            schemas_orfaos.append(schema)
    
    if schemas_orfaos:
        print(f"\n❌ ERRO: {len(schemas_orfaos)} schema(s) órfão(s):")
        
        total_size_bytes = 0
        for schema in schemas_orfaos:
            # Contar tabelas
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, (schema,))
            table_count = cursor.fetchone()[0]
            
            # Calcular tamanho
            try:
                cursor.execute(f"""
                    SELECT SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))
                    FROM pg_tables
                    WHERE schemaname = %s
                """, (schema,))
                size = cursor.fetchone()[0] or 0
                total_size_bytes += size
                size_mb = size / (1024 * 1024)
                print(f"   - {schema:30s} | {table_count:3d} tabelas | {size_mb:8.2f} MB")
            except Exception as e:
                print(f"   - {schema:30s} | {table_count:3d} tabelas | Erro ao calcular tamanho")
        
        total_size_mb = total_size_bytes / (1024 * 1024)
        print(f"\n   📊 Total: {total_size_mb:.2f} MB em schemas órfãos")
        
        print("\n🔧 COMANDOS PARA LIMPAR SCHEMAS ÓRFÃOS:")
        print("   Execute no psql ou Heroku PostgreSQL:")
        print()
        for schema in schemas_orfaos:
            print(f'   DROP SCHEMA IF EXISTS "{schema}" CASCADE;')
        print()
        
        # Gerar script SQL
        script_path = os.path.join(os.path.dirname(__file__), 'limpar_schemas_orfaos.sql')
        with open(script_path, 'w') as f:
            f.write("-- Script para limpar schemas órfãos\n")
            f.write(f"-- Gerado em: {os.popen('date').read().strip()}\n")
            f.write(f"-- Total de schemas: {len(schemas_orfaos)}\n")
            f.write(f"-- Tamanho total: {total_size_mb:.2f} MB\n\n")
            for schema in schemas_orfaos:
                f.write(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;\n')
        print(f"   📄 Script SQL salvo em: {script_path}")
        
    else:
        print("✅ Nenhum schema órfão encontrado")
        
except Exception as e:
    print(f"❌ Erro ao verificar schemas: {e}")
    import traceback
    traceback.print_exc()

# 4. VERIFICAR USUÁRIOS ÓRFÃOS
print("\n4️⃣ VERIFICANDO USUÁRIOS ÓRFÃOS")
print("-" * 80)
try:
    cursor.execute("""
        SELECT u.id, u.username, u.email, u.date_joined
        FROM auth_user u
        WHERE u.is_superuser = FALSE 
          AND u.is_staff = FALSE
          AND NOT EXISTS (
              SELECT 1 FROM superadmin_loja l WHERE l.owner_id = u.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM superadmin_usuariosistema us WHERE us.user_id = u.id
          )
        ORDER BY u.id
    """)
    users_orfaos = cursor.fetchall()
    
    if users_orfaos:
        print(f"❌ ERRO: {len(users_orfaos)} usuário(s) órfão(s):")
        for user_id, username, email, date_joined in users_orfaos:
            print(f"   - ID: {user_id:4d} | Username: {username:20s} | Email: {email}")
            print(f"     Criado em: {date_joined.strftime('%d/%m/%Y %H:%M')}")
        
        print("\n🔧 COMANDOS PARA LIMPAR USUÁRIOS ÓRFÃOS:")
        print("   Execute no Django shell:")
        print("   from django.contrib.auth.models import User")
        for user_id, username, _, _ in users_orfaos:
            print(f"   User.objects.get(id={user_id}).delete()  # {username}")
    else:
        print("✅ Nenhum usuário órfão encontrado")
        
except Exception as e:
    print(f"❌ Erro ao verificar usuários: {e}")

# 5. VERIFICAR ASAAS ÓRFÃOS
print("\n5️⃣ VERIFICANDO ASAAS INTEGRATION ÓRFÃOS")
print("-" * 80)
try:
    # LojaAssinatura órfãs
    cursor.execute("""
        SELECT id, loja_slug, loja_nome
        FROM asaas_integration_lojaassinatura
        ORDER BY id
    """)
    assinaturas = cursor.fetchall()
    
    assinaturas_orfas = []
    for ass_id, loja_slug, loja_nome in assinaturas:
        if loja_slug not in slugs_ativos:
            assinaturas_orfas.append((ass_id, loja_slug, loja_nome))
    
    if assinaturas_orfas:
        print(f"❌ ERRO: {len(assinaturas_orfas)} assinatura(s) Asaas órfã(s):")
        for ass_id, loja_slug, loja_nome in assinaturas_orfas:
            print(f"   - ID: {ass_id:4d} | Slug: {loja_slug:20s} | Nome: {loja_nome}")
        
        print("\n🔧 COMANDOS PARA LIMPAR ASSINATURAS ÓRFÃS:")
        print("   Execute no Django shell:")
        print("   from asaas_integration.models import LojaAssinatura")
        for ass_id, _, _ in assinaturas_orfas:
            print(f"   LojaAssinatura.objects.get(id={ass_id}).delete()")
    else:
        print("✅ Nenhuma assinatura Asaas órfã")
        
except Exception as e:
    print(f"⚠️  Erro ao verificar Asaas (tabela pode não existir): {e}")

# 6. VERIFICAR DIRETÓRIOS DE BACKUP
print("\n6️⃣ VERIFICANDO DIRETÓRIOS DE BACKUP")
print("-" * 80)
try:
    backups_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
    if os.path.exists(backups_dir):
        subdirs = [d for d in os.listdir(backups_dir) if os.path.isdir(os.path.join(backups_dir, d))]
        
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
                print(f"   - {subdir:30s} | {file_count:3d} arquivo(s) | {size_mb:8.2f} MB")
            print(f"\n   📊 Total: {total_size_mb:.2f} MB em backups órfãos")
            
            print("\n🔧 AÇÃO RECOMENDADA:")
            print("   Mover para pasta de arquivamento ou excluir:")
            for subdir, _, _ in dirs_orfaos:
                print(f"   rm -rf backups/{subdir}")
        else:
            print("✅ Nenhum diretório de backup órfão")
    else:
        print("ℹ️  Diretório de backups não existe")
except Exception as e:
    print(f"❌ Erro ao verificar backups: {e}")

# 7. VERIFICAR ARQUIVOS MEDIA
print("\n7️⃣ VERIFICANDO ARQUIVOS MEDIA")
print("-" * 80)
try:
    media_dir = os.path.join(os.path.dirname(__file__), '..', 'media')
    if os.path.exists(media_dir):
        import glob
        
        loja_files = glob.glob(os.path.join(media_dir, '**', 'loja_*'), recursive=True)
        
        if loja_files:
            print(f"ℹ️  {len(loja_files)} arquivo(s) com padrão 'loja_*' encontrado(s)")
            
            slugs_ativos_normalized = set(slug.replace('-', '_') for slug in slugs_ativos)
            
            files_orfaos = []
            for file_path in loja_files:
                file_name = os.path.basename(file_path)
                parts = file_name.split('_')
                if len(parts) >= 2:
                    slug = parts[1]
                    if slug not in slugs_ativos_normalized:
                        size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                        files_orfaos.append((file_path, size))
            
            if files_orfaos:
                print(f"\n⚠️  {len(files_orfaos)} arquivo(s) órfão(s):")
                total_size_mb = 0
                for file_path, size in files_orfaos[:10]:
                    size_mb = size / (1024 * 1024)
                    total_size_mb += size_mb
                    print(f"   - {os.path.basename(file_path):40s} | {size_mb:8.2f} MB")
                if len(files_orfaos) > 10:
                    print(f"   ... e mais {len(files_orfaos) - 10} arquivos")
                print(f"\n   📊 Total: {total_size_mb:.2f} MB")
            else:
                print("✅ Todos os arquivos pertencem a lojas ativas")
        else:
            print("✅ Nenhum arquivo com padrão 'loja_*'")
    else:
        print("ℹ️  Diretório media não existe")
except Exception as e:
    print(f"❌ Erro ao verificar media: {e}")

# Fechar conexão
cursor.close()
conn.close()

# RESUMO FINAL
print("\n" + "=" * 80)
print("📊 RESUMO DA VERIFICAÇÃO")
print("=" * 80)
print(f"""
Lojas ativas no sistema: {len(lojas)}

LEGENDA:
✅ = OK (sem dados órfãos)
⚠️  = Atenção (verificar manualmente)
❌ = Erro (dados órfãos encontrados - requer limpeza)

ARQUIVOS GERADOS:
- limpar_schemas_orfaos.sql (se houver schemas órfãos)

PRÓXIMOS PASSOS:
1. Executar script SQL para limpar schemas órfãos
2. Limpar usuários órfãos via Django shell
3. Limpar assinaturas Asaas órfãs via Django shell
4. Arquivar ou excluir diretórios de backup órfãos
5. Excluir arquivos media órfãos
""")

print("✅ Verificação completa concluída!")
