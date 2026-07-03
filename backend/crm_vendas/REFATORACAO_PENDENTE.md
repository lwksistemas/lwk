# Refatoração Pendente - CRM Vendas

## Status

### ✅ Concluído:
1. **Backend `views.py`** — dividido em módulos por responsabilidade
2. **Frontend pipeline** — `pipeline/page.tsx` usa `useCrmPipelinePage`
3. **Testes backend** — 190+ testes (`crm_vendas.tests`)
4. **PDFs** — smoke proposta, contrato, comissão, financeiro
5. **Webhooks/fila** — Asaas loja + envio assíncrono de documentos
6. **Frontend** — Vitest `lib/crm-*.test.ts` (pipeline, utils, permissões, etc.)
7. **E2E** — helper `e2e/crm-auth.ts` + fluxo autenticado
8. **E2E assinatura** — `e2e/crm-assinatura-publica.spec.ts`
9. **CI** — `crm_vendas.tests` + Vitest CRM + Playwright no workflow Security
10. **DDL hot path** — patches SQL centralizados em `schema_service` + `ensure_crm_atividade_colunas` no release
11. **Isolamento cross-loja** — `test_tenant_access_crm.py` (403 API, `user_can_access_loja`, pool vendedor opt-in)
12. **Cache** — removido decorator morto `invalidate_cache_on_change`; `CacheInvalidationMixin` é o padrão
13. **Google Calendar** — sync create/update/delete enfileirado via `activities_google_sync_queue` (fallback sync inline sem worker)

### 📋 Pendente (baixo risco, opcional):
- **Backend `pdf_proposta_contrato/`** — reduzir duplicação proposta/contrato (funcional, não urgente)
- **Secret E2E** — opcional `CRM_E2E_ASSINATURA_TOKEN` para fluxo assinatura com link real
- **API com tenant Postgres real no CI** — SQLite não materializa `crm_vendas_*` no default; testes de acesso cobrem camada de permissão
- **Pool sem vendedor** — flag `vendedor_include_unassigned_pool=False` por ViewSet se negócio exigir restrição (padrão atual: pool compartilhado)

## Hooks / páginas
- `useCrmPipelinePage.ts` — pipeline (criar, editar, filtros, PDF)
- Modais em `pipeline/components/ModalCriarOportunidade` e `ModalEditarOportunidade`

## Boas práticas aplicadas:
- ✅ Separação por responsabilidade (config, relatórios, assinatura pública)
- ✅ Service layer + fila assíncrona (documentos, Google Calendar, Asaas)
- ✅ Cache com invalidação automática (`CacheInvalidationMixin`)
- ✅ Isolamento multi-tenant (middleware + `LojaIsolationMixin` + testes API)
- ✅ Suite ~190 backend, 9 arquivos Vitest CRM, E2E público + autenticado no CI
