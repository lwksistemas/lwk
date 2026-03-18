# Problema: Migrations Não Criam Tabelas no Schema da Loja

## Situação Atual (v1110)

Sistema NÃO consegue criar lojas CRM. Todas as tentativas desde v1001 falharam.

### Sintomas
- Schema PostgreSQL é criado com sucesso
- `search_path` é configurado corretamente
- Migrations executam SEM erro
- **Schema fica VAZIO** (0 tabelas)
- Tabelas NÃO aparecem nem no schema da loja nem em `public`

### O Que Já Foi Tentado

#### v1001: Backend Customizado + set_session
- ❌ Erro: "set_session cannot be used inside a transaction"

#### v1002-v1004: OPTIONS com search_path
- ✅ search_path confirmado nos logs
- ❌ Schema continua vazio

#### v1005: PGOPTIONS
- ✅ PGOPTIONS definido
- ❌ Schema continua vazio

#### v1006: Correção de Sintaxe
- ✅ Erro de sintaxe corrigido
- ❌ Schema continua vazio

#### v1007: Remover Backend Customizado
- Voltou para ENGINE padrão do Django
- ✅ search_path na URL
- ❌ Schema continua vazio

#### v1008: ALTER DATABASE SET search_path
- ✅ ALTER DATABASE executado com sucesso
- ✅ search_path padrão definido no banco
- ❌ Schema continua vazio

## Diagnóstico

### Problema Raiz
Django `call_command('migrate')` **abre novas conexões** que:
1. Ignoram backend customizado
2. Ignoram PGOPTIONS
3. Ignoram OPTIONS na URL
4. Ignoram ALTER DATABASE (Heroku usa PgBouncer)

### Por Que Funcionava Antes?
O sistema funcionava ANTES do commit 5fcce997 (17/03/2026) que adicionou o backend customizado.

**HIPÓTESE**: O problema NÃO é o backend customizado, mas algo que mudou no Heroku ou no Django que faz migrations ignorarem search_path.

## Soluções Possíveis

### Opção 1: Executar SQL Manualmente (RECOMENDADO)
Em vez de `call_command('migrate')`, executar o SQL das migrations diretamente:

```python
# 1. Obter SQL das migrations
sql = call_command('sqlmigrate', app, migration_name, '--database', database_name)

# 2. Executar no schema correto
with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO "{schema_name}", public')
    cursor.execute(sql)
```

### Opção 2: Criar Tabelas Manualmente
Copiar estrutura de uma loja existente:

```sql
-- Copiar estrutura de public para schema da loja
CREATE TABLE "loja_xxx".stores_store (LIKE public.stores_store INCLUDING ALL);
-- Repetir para todas as tabelas
```

### Opção 3: Usar django-tenants
Migrar para django-tenants que gerencia schemas automaticamente.

### Opção 4: Rollback Completo
Reverter para versão anterior ao commit 5fcce997 que funcionava.

## Próximos Passos

1. **URGENTE**: Verificar se há lojas CRM funcionando em produção
2. Testar Opção 1 (SQL manual) em desenvolvimento
3. Se Opção 1 funcionar, fazer deploy
4. Se falhar, considerar Opção 4 (rollback)

## Logs Relevantes

```
✅ search_path padrão definido no banco: loja_34787081845,public
Migrations aplicadas: stores
Migrations aplicadas: products  
Migrations aplicadas: crm_vendas
✅ search_path padrão do banco restaurado para public
❌ ERRO CRÍTICO: Schema 'loja_34787081845' está VAZIO após migrations!
```

## Impacto

- Sistema NÃO pode criar novas lojas CRM
- Lojas existentes continuam funcionando
- Problema afeta apenas criação de novas lojas
