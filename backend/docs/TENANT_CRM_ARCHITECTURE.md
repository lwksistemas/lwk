# Multi-tenant CRM: arquitetura e convenções

Este documento fixa a ordem de resolução de tenant e os pontos de extensão para evitar regressões (listas vazias, cache errado, slug vs ID desatualizado).

## Resolução de loja (backend)

1. **Thread-local**: `tenants.middleware.get_current_loja_id()` e `get_current_tenant_db()` — preenchidos por requisição.
2. **Middleware** (`TenantMiddleware`): limpa o contexto no início da requisição e resolve loja por URL/header.
3. **Headers HTTP** (quando ainda não há contexto coerente): usar **`ensure_loja_context(request)`** — mesma regra que o middleware:
   - **`X-Tenant-Slug` antes de `X-Loja-ID`** (o slug reflete a loja “ativa” no app; o ID no cliente pode ficar obsoleto).
4. **Helpers**:
   - `get_loja_from_context(request)` em `crm_vendas/utils.py` deve preferir `ensure_loja_context` em vez de reimplementar leitura de headers.
   - `get_current_vendedor_id` / `is_owner` alinham tenant com `ensure_loja_context` quando necessário.

## Fonte canônica de imports

- **`get_current_loja_id`**: sempre `tenants.middleware` (não usar módulos inexistentes ou duplicados).

## ViewSets e isolamento

- **`BaseModelViewSet`** (`core/views.py`): chama `ensure_loja_context`, valida `loja_id` para modelos com `loja_id`, aplica `is_active` quando o modelo tem o campo.
- **Managers** (`LojaIsolationManager` / `LeadManager`): filtram por `loja_id` do contexto.
- **`LeadViewSet`**: usa `super().get_queryset()` para herdar validação de loja; mantém exceção de **owner** no `retrieve` antes do `filter_by_vendedor`.

## Cache (`crm_vendas/cache.py`)

- **`CRMCacheManager.invalidate`**: obtém `loja_id` de `tenants.middleware.get_current_loja_id` quando não é passado explicitamente, para invalidação consistente com o tenant atual.

## Frontend

- Headers de tenant devem ser centralizados no cliente de API (ex.: `frontend/lib/api-client.ts`).
- Enviar **`X-Tenant-Slug` e `X-Loja-ID`** quando ambos existirem: o backend resolve **slug antes de ID**; o ID cobre requisições em que o slug ainda não foi enviado (evita respostas paginadas vazias ~52 bytes).

## Views de função (`crm_me`, `dashboard_data`)

- Chamar **`ensure_loja_context(request)`** antes de `get_current_loja_id()` para alinhar thread-local aos headers quando o middleware não tiver aplicado o tenant (ordem de middlewares / timing).
