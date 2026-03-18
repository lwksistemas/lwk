# Solução Definitiva: Problema Ambiental Confirmado

## Conclusão

**PROBLEMA É AMBIENTAL, NÃO DO CÓDIGO**

- Código exato que funcionava (commit 0da66668) NÃO funciona mais
- Rollback completo falhou
- Algo mudou no ambiente (Heroku/PostgreSQL/Django)

## Solução: Criar Tabelas Manualmente com SQL

Já que `call_command('migrate')` ignora `search_path`, vamos criar as tabelas diretamente com SQL.

### Implementação

```python
def aplicar_migrations_manual(loja, schema_name, apps_to_migrate):
    """
    Cria tabelas manualmente copiando estrutura de public.
    """
    from django.db import connections
    
    conn = connections[loja.database_name]
    conn.ensure_connection()
    
    with conn.cursor() as cursor:
        # Para cada app, copiar tabelas de public para schema
        for app in apps_to_migrate:
            # Buscar tabelas do app em public
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE %s
                AND table_type = 'BASE TABLE'
            """, [f'{app}_%'])
            
            tabelas = [row[0] for row in cursor.fetchall()]
            
            for tabela in tabelas:
                # Criar tabela no schema copiando estrutura
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS "{schema_name}".{tabela} 
                    (LIKE public.{tabela} INCLUDING ALL)
                ''')
                
                logger.info(f"✅ Tabela {tabela} criada em {schema_name}")
        
        # Criar django_migrations no schema
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{schema_name}".django_migrations (
                id SERIAL PRIMARY KEY,
                app VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                applied TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        ''')
        
        # Copiar registros de migrations de public
        for app in apps_to_migrate:
            cursor.execute(f'''
                INSERT INTO "{schema_name}".django_migrations (app, name, applied)
                SELECT app, name, applied 
                FROM public.django_migrations 
                WHERE app = %s
                ON CONFLICT DO NOTHING
            ''', [app])
```

### Vantagens
- ✅ Não depende de `call_command('migrate')`
- ✅ Controle total sobre onde tabelas são criadas
- ✅ Funciona independente de search_path
- ✅ Rápido e confiável

### Desvantagens
- ⚠️ Precisa que tabelas existam em public (template)
- ⚠️ Não executa código Python das migrations
- ⚠️ Precisa manter sincronizado com mudanças no schema

## Alternativa: Executar SQL das Migrations

```python
from django.core.management import call_command
from io import StringIO

# Obter SQL de cada migration
for app in apps_to_migrate:
    # Listar migrations do app
    out = StringIO()
    call_command('showmigrations', app, '--plan', stdout=out)
    migrations = parse_migrations(out.getvalue())
    
    for migration in migrations:
        # Obter SQL da migration
        sql_out = StringIO()
        call_command('sqlmigrate', app, migration, stdout=sql_out)
        sql = sql_out.getvalue()
        
        # Executar SQL no schema correto
        with conn.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            cursor.execute(sql)
```

## Recomendação

Implementar **Solução 1** (copiar estrutura) por ser mais simples e confiável.

## Próximos Passos

1. Implementar função `aplicar_migrations_manual()`
2. Substituir `call_command('migrate')` por essa função
3. Testar criação de loja
4. Se funcionar, fazer deploy
5. Limpar lojas órfãs (IDs 108-120)
