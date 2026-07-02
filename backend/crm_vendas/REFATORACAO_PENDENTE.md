# Refatoração Pendente - CRM Vendas

## Status

### ✅ Concluído:
1. **Backend `views.py`** — dividido em módulos por responsabilidade
2. **Frontend pipeline** — `pipeline/page.tsx` usa `useCrmPipelinePage` (247 linhas)
3. **Testes backend** — 153+ testes unitários/smoke + integração API (`test_api_crm_integration.py`)
4. **PDFs** — smoke proposta, contrato, comissão, financeiro
5. **Webhooks/fila** — Asaas loja + envio assíncrono de documentos
6. **Frontend** — `lib/crm-pipeline.test.ts` + E2E smoke ampliado (`e2e/crm-smoke.spec.ts`)

### 📋 Pendente (baixo risco, opcional):
- **Backend `pdf_proposta_contrato/`** — reduzir duplicação proposta/contrato (funcional, não urgente)
- **E2E completo** — fluxo pipeline → proposta → assinatura com credenciais em CI (requer secrets)

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
- ✅ Suite de testes alinhada ao nível produção (~160+ backend)
