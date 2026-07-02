# Refatoração Pendente - CRM Vendas

## Status

### ✅ Concluído:
1. **Backend `views.py`** — dividido em módulos por responsabilidade
2. **Frontend pipeline** — `pipeline/page.tsx` usa `useCrmPipelinePage` (247 linhas)
3. **Testes backend** — 160+ testes unitários/smoke + integração API (`test_api_crm_integration.py`, `test_api_crm_documentos.py`)
4. **PDFs** — smoke proposta, contrato, comissão, financeiro
5. **Webhooks/fila** — Asaas loja + envio assíncrono de documentos
6. **Frontend** — Vitest `lib/crm-*.test.ts` (pipeline, utils, permissões, etc.)
7. **E2E** — helper `e2e/crm-auth.ts` + fluxo autenticado pipeline → leads → propostas → contratos → financeiro
8. **E2E assinatura** — `e2e/crm-assinatura-publica.spec.ts` (token inválido + opcional `CRM_E2E_ASSINATURA_TOKEN`)
9. **CI** — `crm_vendas.tests` + Vitest CRM + Playwright smoke público no workflow Security
10. **API cadastros/config** — smoke contas, contatos, atividades, `GET /config/`
11. **Vitest** — `crm-documento-valores`, `crm-periodos`
12. **CI E2E autenticado** — job opcional quando secrets `CRM_E2E_*` configurados no repositório

### 📋 Pendente (baixo risco, opcional):
- **Backend `pdf_proposta_contrato/`** — reduzir duplicação proposta/contrato (funcional, não urgente)
- **Secrets E2E** — configurados no GitHub (`CRM_E2E_EMAIL`, `CRM_E2E_PASSWORD`, `CRM_E2E_LOJA_SLUG=vendasbeta`); opcional `CRM_E2E_ASSINATURA_TOKEN`
- **CI** — `lxml` no `requirements.txt`; job E2E autenticado sem `if` inválido em secrets
- **API com tenant real** — migrations CRM não rodam em SQLite; smoke com mocks cobre rotas principais

## Hooks / páginas
- `useCrmPipelinePage.ts` — pipeline (criar, editar, filtros, PDF)
- Modais em `pipeline/components/ModalCriarOportunidade` e `ModalEditarOportunidade`

## Boas práticas aplicadas:
- ✅ Separação por responsabilidade (config, relatórios, assinatura pública)
- ✅ Re-exports para compatibilidade (urls.py não precisou mudar)
- ✅ Hooks customizados para lógica complexa
- ✅ Componentes reutilizáveis (modais, badges, seletores)
- ✅ Mixins DRY no backend
- ✅ Cache com invalidação automática
- ✅ Isolamento multi-tenant seguro
- ✅ Suite de testes alinhada ao nível produção (~175+ backend, 9 arquivos Vitest CRM, E2E público + autenticado opcional no CI)
