# Refatoração Pendente - CRM Vendas

## Status

### ✅ Concluído:
1. **Backend `views.py`** — dividido em 4 arquivos (2337 → 1303 + 746 + 133 + 258)
2. **Frontend hooks** — lógica de criar/editar oportunidade extraída para hooks reutilizáveis

### 📋 Pendente (baixo risco, fazer quando necessário):
- **Frontend `pipeline/page.tsx`** — usar os hooks criados para reduzir o arquivo
- **Backend `pdf_proposta_contrato.py`** — duplicação entre proposta/contrato (funcional, não urgente)

## Hooks criados:
- `usePipelineCriarOportunidade.ts` — toda lógica de criação de oportunidade
- `usePipelineEditarOportunidade.ts` — toda lógica de edição de oportunidade

## Boas práticas aplicadas:
- ✅ Separação por responsabilidade (config, relatórios, assinatura pública)
- ✅ Re-exports para compatibilidade (urls.py não precisou mudar)
- ✅ Hooks customizados para lógica complexa
- ✅ Componentes reutilizáveis (modais, badges, seletores)
- ✅ Mixins DRY no backend
- ✅ Cache com invalidação automática
- ✅ Isolamento multi-tenant seguro
