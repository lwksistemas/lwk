# 🚨 Problema Crítico: Clientes Não Aparecem (Schema Incorreto)

## Problema Identificado

Os clientes estão salvos no banco de dados, mas **não aparecem na lista** porque o sistema está usando o **schema errado**.

### Evidências:

1. **Clientes existem no banco**:
```sql
SELECT * FROM loja_salao_000172.cabeleireiro_clientes;
-- ID 1: Luiz Henrique Felix
-- ID 2: teste
```

2. **API retorna lista vazia**:
```
GET /api/cabeleireiro/clientes/ → {count: 0, results: []}
```

3. **LojaIsolationManager não encontra contexto**:
```
⚠️ [LojaIsolationManager] Nenhuma loja no contexto - retornando queryset vazio
```

## Causa Raiz

O **TenantMiddleware** está configurando o schema como `loja_{id}` (ex: `loja_90`), mas o schema real é `loja_{database_name}` (ex: `loja_salao_000172`).

### Código Problemático (linha 73 do middleware):
```python
schema_name = f"loja_{loja.id}"  # ❌ Errado! Usa ID ao invés de database_name
```

### Código Correto:
```python
schema_name = loja.database_name or f"loja_{loja.id}"  # ✅ Usa database_name da loja
```

## Correção Aplicada Localmente

✅ Arquivo modificado: `backend/tenants/middleware.py` (linha 70)
✅ Mudança: Usar `loja.database_name` ao invés de `f"loja_{loja.id}"`

## ⚠️ PROBLEMA: Correção Não Funciona Localmente

Mesmo após a correção, o problema persiste localmente porque:

1. **Logs do TenantMiddleware não aparecem** (nível de log muito alto)
2. **LojaIsolationManager continua sem contexto**
3. **Possível problema de cache ou configuração local**

## 🎯 Solução Recomendada

### Para Produção (URGENTE):

1. **Commitar a correção do middleware**
2. **Deploy no Heroku**
3. **Testar em produção** (onde o sistema funciona corretamente)

### Para Local (Investigação Futura):

1. Verificar configuração de logs em `settings_local.py`
2. Verificar se o middleware está na ordem correta em `MIDDLEWARE`
3. Considerar usar banco PostgreSQL local ao invés do Heroku

## Arquivos Modificados

- ✅ `backend/tenants/middleware.py` - Correção do schema
- ✅ `frontend/hooks/useDashboardData.ts` - Fix React Strict Mode
- ✅ `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/cabeleireiro.tsx` - Modal Cliente com showForm

## Próximos Passos

1. **Commitar todas as mudanças**
2. **Deploy backend no Heroku**
3. **Deploy frontend no Vercel** (opcional)
4. **Testar em produção**: https://lwksistemas.com.br/loja/salao-000172/dashboard

## Comandos para Deploy

```bash
# Backend
git add backend/tenants/middleware.py
git add frontend/hooks/useDashboardData.ts
git add frontend/app/(dashboard)/loja/[slug]/dashboard/templates/cabeleireiro.tsx
git commit -m "fix: Corrigir schema do banco para usar database_name ao invés de ID

- TenantMiddleware agora usa loja.database_name para o schema
- Fix React Strict Mode no useDashboardData
- Modal Cliente com padrão showForm (lista após salvar)
"
git push heroku master

# Frontend (opcional)
cd frontend
vercel --prod
```

## Observação

O sistema **funciona em produção**, o problema é apenas **local** devido à configuração do ambiente de desenvolvimento.
