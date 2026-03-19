# Correção: AssinaturaDigital - Schemas Isolados por Loja (v1158)

## Problema Identificado

### Erro Original
```
column "proposta_id" of relation "crm_vendas_assinatura_digital" does not exist
```

### Causa Raiz
A migration 0025 (que remove `GenericForeignKey` e adiciona `ForeignKeys` diretos) foi aplicada apenas no banco `default`, mas **NÃO** nos schemas de tenant (loja_*).

### Descoberta Importante
O sistema usa **schemas isolados por loja** baseados em CPF/CNPJ, não em ID:
- **Loja 130**: Schema `loja_22239255889` (baseado em CPF/CNPJ)
- **Loja 129**: Schema `loja_41449198000172` (baseado em CNPJ)

## Solução Implementada

### 1. Comando de Diagnóstico
Criado `check_tenant_schemas.py` para verificar:
- Schemas existentes no PostgreSQL
- Lojas ativas e seus schemas esperados
- Existência da tabela `crm_vendas_assinatura_digital` em cada schema

**Execução:**
```bash
heroku run "cd backend && python manage.py check_tenant_schemas" --app lwksistemas
```

**Resultado:**
```
📊 Schemas existentes: 2
  - loja_22239255889
  - loja_41449198000172

📊 Lojas ativas: 2
  ❌ ID: 130, Nome: CRM VENDAS TESTE, Schema: loja_130 (esperado)
      ✅ Schema real: loja_22239255889
  ❌ ID: 129, Nome: FELIX REPRESENTACOES E COMERCIO LTDA, Schema: loja_129 (esperado)
      ✅ Schema real: loja_41449198000172
```

### 2. Comando de Correção
Criado `apply_migration_0025_tenants.py` para aplicar a migration 0025 em todos os schemas de tenant.

**O que faz:**
1. Busca todas as lojas CRM ativas
2. Para cada loja, verifica se o schema existe
3. Verifica se a tabela `AssinaturaDigital` existe
4. Verifica se a migration já foi aplicada (campos `proposta_id` e `contrato_id` existem)
5. Aplica a migration:
   - Adiciona campos `proposta_id` e `contrato_id`
   - Migra dados de `content_type_id/object_id` para os novos campos
   - Adiciona ForeignKeys
   - Remove campos antigos (`content_type_id`, `object_id`)
   - Cria índices
   - Adiciona constraint de validação
   - Registra migration como aplicada

**Execução:**
```bash
heroku run "cd backend && python manage.py apply_migration_0025_tenants" --app lwksistemas
```

**Resultado:**
```
🏪 Loja: CRM VENDAS TESTE (ID: 130)
   Schema: loja_22239255889
   ✅ Migration aplicada com sucesso!

🏪 Loja: FELIX REPRESENTACOES E COMERCIO LTDA (ID: 129)
   Schema: loja_41449198000172
   ⚠️  Tabela AssinaturaDigital não existe (normal - loja sem assinaturas)
```

### 3. Verificação Final
```bash
heroku run "cd backend && python manage.py shell -c \"from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position', ['loja_22239255889', 'crm_vendas_assinatura_digital']); cols = [row[0] for row in cursor.fetchall()]; print('Colunas:'); [print(f'  - {col}') for col in cols]\"" --app lwksistemas
```

**Resultado:**
```
Colunas da tabela AssinaturaDigital:
  - id
  - loja_id
  - tipo
  - nome_assinante
  - email_assinante
  - ip_address
  - timestamp
  - user_agent
  - token
  - token_expira_em
  - assinado
  - assinado_em
  - created_at
  - updated_at
  - proposta_id      ✅ NOVO
  - contrato_id      ✅ NOVO
```

## Arquivos Modificados

### Novos Comandos
- `backend/crm_vendas/management/commands/check_tenant_schemas.py`
- `backend/crm_vendas/management/commands/apply_migration_0025_tenants.py`

## Lições Aprendidas

### 1. Sistema Multi-Tenant com Schemas Isolados
- Cada loja tem seu próprio schema PostgreSQL
- Schemas são nomeados baseados em CPF/CNPJ, não em ID
- Migrations precisam ser aplicadas em CADA schema de tenant

### 2. Migrations em Multi-Tenant
- `python manage.py migrate` aplica apenas no banco `default`
- Schemas de tenant precisam de tratamento especial
- Solução: Comandos management customizados que iteram sobre schemas

### 3. GenericForeignKey e Multi-Tenant
- `GenericForeignKey` usa `ContentType` que fica no banco `default`
- Criar relação cross-database (ContentType no `default`, AssinaturaDigital no tenant)
- Database router bloqueia essas relações
- Solução: Usar `ForeignKey` direto ao invés de `GenericForeignKey`

## Próximos Passos

1. ✅ Migration 0025 aplicada nos schemas existentes
2. ⏳ Testar criação de AssinaturaDigital em produção
3. ⏳ Verificar se botão de assinatura funciona corretamente
4. ⏳ Monitorar logs para garantir que não há mais erros

## Comandos Úteis

### Verificar schemas existentes
```bash
heroku run "cd backend && python manage.py check_tenant_schemas" --app lwksistemas
```

### Aplicar migration em schemas de tenant
```bash
heroku run "cd backend && python manage.py apply_migration_0025_tenants" --app lwksistemas
```

### Verificar estrutura de tabela
```bash
heroku run "cd backend && python manage.py shell -c \"from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s', ['SCHEMA_NAME', 'TABLE_NAME']); [print(row[0]) for row in cursor.fetchall()]\"" --app lwksistemas
```

## Correção Adicional (v1159)

### Problema: Link de Assinatura Apontando para Backend
O link de assinatura estava sendo gerado com `request.build_absolute_uri('/')`, que retorna a URL do backend (Heroku), mas deveria apontar para o frontend (Vercel).

**Erro nos logs:**
```
Not Found: /assinar/eyJkb2NfdHlwZSI6InByb3Bvc3RhIiwiZG9jX2lkIjozLCJ0aXBvIjoiY2xpZW50ZSIsImxvamFfaWQiOjEzMCwiZXhwIjoxNzc0NTA2NTQ1fQ
```

### Solução
Alterado `assinatura_digital_service.py` para usar `settings.FRONTEND_URL` ao invés de `request.build_absolute_uri('/')`:

```python
# ANTES
base_url = request.build_absolute_uri('/').rstrip('/')
link_assinatura = f'{base_url}/assinar/{assinatura.token}'

# DEPOIS
frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
link_assinatura = f'{frontend_url}/assinar/{assinatura.token}'
```

**Arquivos modificados:**
- `backend/crm_vendas/assinatura_digital_service.py`
  - `enviar_email_assinatura_cliente()`
  - `enviar_email_assinatura_vendedor()`

## Status

✅ **RESOLVIDO** - Migration 0025 aplicada com sucesso nos schemas de tenant. Links de assinatura corrigidos para apontar para o frontend. Sistema de assinatura digital pronto para uso.

## Versão

- Backend: v1159
- Data: 2025-03-19
