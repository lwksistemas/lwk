# Instruções: Verificar Dados Órfãos no Heroku

## Contexto
Você excluiu 7 lojas de teste. Precisamos verificar se ficaram dados órfãos no sistema:
- Schemas PostgreSQL
- Usuários sem lojas
- Assinaturas Asaas
- Diretórios de backup
- Arquivos media

## Método 1: Script Python Completo (Recomendado)

### Passo 1: Fazer upload do script para o Heroku

```bash
git add backend/verificar_orfaos_simples.py
git commit -m "feat: Script para verificar dados órfãos"
git push heroku master
```

### Passo 2: Executar no Heroku

```bash
heroku run "cd backend && python verificar_orfaos_simples.py" --app lwksistemas
```

## Método 2: Verificação Manual via SQL

### Conectar ao PostgreSQL do Heroku

```bash
heroku pg:psql --app lwksistemas
```

### 1. Listar lojas ativas

```sql
SELECT id, slug, nome, database_name 
FROM superadmin_loja 
ORDER BY id;
```

### 2. Verificar schemas órfãos

```sql
-- Listar todos os schemas que começam com 'loja_'
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'loja_%'
ORDER BY schema_name;
```

Compare com os `database_name` das lojas ativas. Schemas que não correspondem a nenhuma loja são órfãos.

### 3. Calcular tamanho dos schemas órfãos

```sql
-- Substituir 'loja_XXXXX' pelo nome do schema órfão
SELECT 
    schemaname,
    pg_size_pretty(SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))::bigint) as size
FROM pg_tables
WHERE schemaname = 'loja_XXXXX'
GROUP BY schemaname;
```

### 4. Excluir schema órfão (CUIDADO!)

```sql
-- ATENÇÃO: Isso é irreversível!
-- Substituir 'loja_XXXXX' pelo nome do schema órfão
DROP SCHEMA IF EXISTS "loja_XXXXX" CASCADE;
```

### 5. Verificar usuários órfãos

```sql
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
ORDER BY u.id;
```

### 6. Verificar assinaturas Asaas órfãs

```sql
SELECT a.id, a.loja_slug, a.loja_nome
FROM asaas_integration_lojaassinatura a
WHERE NOT EXISTS (
    SELECT 1 FROM superadmin_loja l WHERE l.slug = a.loja_slug
)
ORDER BY a.id;
```

## Método 3: Django Shell

### Conectar ao Django shell no Heroku

```bash
heroku run "cd backend && python manage.py shell" --app lwksistemas
```

### Verificar schemas órfãos

```python
from django.db import connection
from superadmin.models import Loja

# Listar lojas ativas
lojas = Loja.objects.all()
print(f"Lojas ativas: {lojas.count()}")
for loja in lojas:
    print(f"  - {loja.slug} ({loja.database_name})")

# Listar schemas no PostgreSQL
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'loja_%'
        ORDER BY schema_name
    """)
    schemas = [row[0] for row in cursor.fetchall()]
    print(f"\nSchemas encontrados: {len(schemas)}")
    for schema in schemas:
        print(f"  - {schema}")

# Identificar órfãos
db_names = set(loja.database_name for loja in lojas)
orfaos = [s for s in schemas if s not in db_names]
print(f"\nSchemas órfãos: {len(orfaos)}")
for orfao in orfaos:
    print(f"  - {orfao}")
```

### Excluir schemas órfãos

```python
from django.db import connection

schemas_orfaos = ['loja_XXXXX', 'loja_YYYYY']  # Substituir pelos nomes reais

for schema in schemas_orfaos:
    with connection.cursor() as cursor:
        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        print(f"✅ Schema {schema} excluído")
```

### Verificar e limpar usuários órfãos

```python
from django.contrib.auth.models import User
from superadmin.models import Loja, UsuarioSistema

# Buscar usuários órfãos
users_orfaos = User.objects.filter(
    is_superuser=False,
    is_staff=False,
    lojas_owned__isnull=True
).exclude(
    perfil_sistema__isnull=False
)

print(f"Usuários órfãos: {users_orfaos.count()}")
for user in users_orfaos:
    print(f"  - ID: {user.id} | Username: {user.username} | Email: {user.email}")

# Excluir usuários órfãos (CUIDADO!)
# for user in users_orfaos:
#     user.delete()
#     print(f"✅ Usuário {user.username} excluído")
```

### Verificar e limpar assinaturas Asaas órfãs

```python
from asaas_integration.models import LojaAssinatura
from superadmin.models import Loja

# Slugs das lojas ativas
slugs_ativos = set(Loja.objects.values_list('slug', flat=True))

# Buscar assinaturas órfãs
assinaturas_orfas = []
for ass in LojaAssinatura.objects.all():
    if ass.loja_slug not in slugs_ativos:
        assinaturas_orfas.append(ass)

print(f"Assinaturas órfãs: {len(assinaturas_orfas)}")
for ass in assinaturas_orfas:
    print(f"  - ID: {ass.id} | Slug: {ass.loja_slug} | Nome: {ass.loja_nome}")

# Excluir assinaturas órfãs (CUIDADO!)
# for ass in assinaturas_orfas:
#     ass.delete()
#     print(f"✅ Assinatura {ass.loja_slug} excluída")
```

## Verificação de Arquivos (Local)

### Diretórios de backup

```bash
# Listar diretórios de backup
ls -lh backups/

# Identificar órfãos comparando com lojas ativas
# Excluir diretórios órfãos
# rm -rf backups/SLUG_ORFAO
```

### Arquivos media

```bash
# Buscar arquivos com padrão loja_*
find media/ -name "loja_*" -type f

# Excluir arquivos órfãos
# rm media/path/to/loja_ORFAO_*
```

## Cloudinary (Manual)

1. Acessar: https://console.cloudinary.com/
2. Ir para Media Library
3. Buscar pastas com nomes de lojas excluídas
4. Excluir pastas órfãs manualmente

## Checklist de Verificação

- [ ] Schemas PostgreSQL órfãos identificados e excluídos
- [ ] Usuários órfãos identificados e excluídos
- [ ] Assinaturas Asaas órfãs identificadas e excluídas
- [ ] Profissionais/Vendedores órfãos identificados e excluídos
- [ ] Financeiro/Pagamentos órfãos identificados e excluídos
- [ ] Diretórios de backup órfãos arquivados ou excluídos
- [ ] Arquivos media órfãos excluídos
- [ ] Cloudinary verificado e limpo

## Observações Importantes

1. **Schemas PostgreSQL**: São os maiores consumidores de espaço. Priorize a limpeza deles.
2. **Usuários órfãos**: Podem bloquear a criação de novas lojas com o mesmo username.
3. **Asaas**: Dados no Asaas (API externa) não são excluídos automaticamente. Considere cancelar clientes/pagamentos manualmente no painel do Asaas.
4. **Backups**: Considere arquivar em vez de excluir, caso precise restaurar dados no futuro.
5. **Cloudinary**: Imagens no Cloudinary não são excluídas automaticamente. Limpeza manual necessária.

## Automação Futura

Considere criar um comando Django para automatizar a limpeza:

```bash
python manage.py limpar_orfaos --dry-run  # Simular
python manage.py limpar_orfaos --execute  # Executar
```
