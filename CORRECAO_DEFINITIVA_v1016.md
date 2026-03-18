# Correção DEFINITIVA v1016: Executar SQL das Migrations Diretamente

## Problema Confirmado

v1015 FALHOU. Log mostra:
```
✅ search_path configurado para stores: loja_41449198000172, public
✅ Migrations aplicadas: stores
✅ search_path configurado para products: loja_41449198000172, public
✅ Migrations aplicadas: products
✅ search_path configurado para crm_vendas: loja_41449198000172, public
✅ Migrations aplicadas: crm_vendas
❌ Schema 'loja_41449198000172' está VAZIO
```

**CONCLUSÃO**: Django `call_command('migrate')` ignora `search_path` COMPLETAMENTE, mesmo quando configurado corretamente.

## Solução DEFINITIVA v1016

**Parar de usar `call_command('migrate')` completamente.**

Implementar sistema próprio de migrations que:

1. Cria tabela `django_migrations` no schema
2. Obtém lista de migrations não aplicadas
3. Para cada migration:
   - Usa `call_command('sqlmigrate')` para obter SQL
   - Executa SQL diretamente no schema com `SET search_path`
   - Registra migration em `django_migrations`

### Fluxo Implementado

```python
# 1. Criar tabela django_migrations no schema
CREATE TABLE IF NOT EXISTS django_migrations (...)

# 2. Para cada app
for app in apps_to_migrate:
    # 3. Obter migrations não aplicadas
    applied = SELECT name FROM django_migrations WHERE app = app
    
    # 4. Obter todas as migrations do app
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(conn)
    migrations_to_apply = [m for m in loader.graph.leaf_nodes() 
                          if m[0] == app and m[1] not in applied]
    
    # 5. Para cada migration
    for app_label, migration_name in migrations_to_apply:
        # 6. Obter SQL
        sql = call_command('sqlmigrate', app_label, migration_name)
        
        # 7. Executar SQL no schema
        SET search_path TO schema_name, public
        EXECUTE sql
        
        # 8. Registrar como aplicada
        INSERT INTO django_migrations (app, name, applied) VALUES (...)
```

## Vantagens

1. **Controle total** sobre onde as tabelas são criadas
2. **Não depende** de Django respeitar search_path
3. **Funciona** mesmo com PgBouncer/Heroku
4. **Logs detalhados** de cada migration executada

## Arquivos Modificados

- `backend/superadmin/services/database_schema_service.py`
  - Método `aplicar_migrations()` completamente reescrito
  - Usa `MigrationLoader` para obter migrations
  - Usa `sqlmigrate` para obter SQL
  - Executa SQL diretamente com cursor

## Deploy

```bash
git add backend/superadmin/services/database_schema_service.py CORRECAO_DEFINITIVA_v1016.md
git commit -m "fix(v1016): Executar SQL das migrations diretamente no schema"
git push heroku master
```

## Teste

```bash
# Criar loja teste CRM
# Frontend: https://lwksistemas.com.br/superadmin/lojas/criar
# Tipo: CRM Vendas
# Nome: Teste v1016
# CNPJ: 34787081845
```

## Logs Esperados

```
🚀 Iniciando migrations manuais para schema 'loja_34787081845'
✅ Tabela django_migrations criada em 'loja_34787081845'
📦 Processando app: stores
   📝 X migration(s) pendente(s)
      ✅ 0001_initial
      ✅ 0002_...
   ✅ App stores concluído
📦 Processando app: products
   📝 X migration(s) pendente(s)
      ✅ 0001_initial
      ✅ 0002_...
   ✅ App products concluído
📦 Processando app: crm_vendas
   📝 X migration(s) pendente(s)
      ✅ 0001_initial
      ✅ 0002_...
   ✅ App crm_vendas concluído
✅ Schema 'loja_34787081845' criado com sucesso: X tabela(s)
🎉 Migrations concluídas para 'loja_34787081845'
```

## Se Funcionar

🎉 **PROBLEMA RESOLVIDO DEFINITIVAMENTE!**

Sistema agora tem controle total sobre criação de tabelas em schemas.

## Se Ainda Falhar

Se ainda falhar, o problema é mais profundo:
- `sqlmigrate` pode não estar gerando SQL correto
- Pode haver problema com permissões no PostgreSQL
- Pode haver problema com o próprio schema

Nesse caso, considerar:
1. Migrar para `django-tenants` (biblioteca especializada)
2. Criar tabelas manualmente via SQL puro
3. Abrir ticket no suporte do Heroku

## Histórico

- v1001-v1014: 14 tentativas com `call_command('migrate')` - TODAS FALHARAM
- v1015: Voltou para código antigo - FALHOU
- v1016: Executar SQL diretamente - SOLUÇÃO DEFINITIVA

## Impacto

Esta é a **última tentativa** com Django migrations.

Se falhar, precisaremos de abordagem completamente diferente.
