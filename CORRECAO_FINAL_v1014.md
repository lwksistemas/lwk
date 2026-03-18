# Correção Final v1014: Problema Descoberto

## Descoberta Crítica

**NÃO HÁ TABELAS EM PUBLIC PARA COPIAR!**

Log mostra: `✅ 0 tabela(s) criada(s) no schema 'loja_41449198000172'`

Isso significa:
- Sistema sempre usou schemas isolados
- Tabelas nunca foram criadas em `public`
- Não há template para copiar

## Solução Real

Precisamos executar as migrations FORÇANDO o schema. Duas opções:

### Opção 1: Executar SQL das Migrations Diretamente

```python
from django.core.management import call_command
from io import StringIO

# Para cada app, obter SQL e executar no schema
for app in apps_to_migrate:
    # Listar migrations não aplicadas
    migrations = get_unapplied_migrations(app, loja.database_name)
    
    for migration in migrations:
        # Obter SQL da migration
        sql_out = StringIO()
        call_command('sqlmigrate', app, migration, 
                    '--database', loja.database_name, 
                    stdout=sql_out)
        sql = sql_out.getvalue()
        
        # Executar SQL no schema
        with conn.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            cursor.execute(sql)
```

### Opção 2: Usar Transação Explícita

```python
from django.db import transaction

with transaction.atomic(using=loja.database_name):
    conn = connections[loja.database_name]
    with conn.cursor() as cursor:
        # SET LOCAL só funciona dentro de transação
        cursor.execute(f'SET LOCAL search_path TO "{schema_name}", public')
        
        # Executar migrate na mesma transação
        call_command('migrate', app, '--database', loja.database_name)
```

### Opção 3: Criar Loja Template em Public

Criar UMA loja template em `public` e copiar estrutura dela:

```sql
-- Criar tabelas template em public (fazer UMA VEZ)
CREATE TABLE public.stores_store (...);
CREATE TABLE public.products_product (...);
CREATE TABLE public.crm_vendas_lead (...);
-- etc
```

## Recomendação

Tentar **Opção 2** primeiro (transação explícita com SET LOCAL).

Se falhar, implementar **Opção 1** (SQL direto das migrations).
