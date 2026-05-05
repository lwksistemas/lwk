# Refatoração Pendente - CRM Vendas

## Backend: views.py (2337 linhas → dividir em ~800 cada)

### Plano:
1. **views_config.py** — Extrair: `crm_config`, `crm_config_asaas_test`, `crm_config_issnet_test`, `crm_busca`, `LoginConfigView`
2. **views_relatorios.py** — Extrair: `gerar_relatorio`, `dashboard_data`
3. **views_assinatura_publica.py** — Extrair: `AssinaturaPublicaView`, `AssinaturaPdfView`, `_configurar_tenant_para_assinatura_publica`
4. **views.py** — Manter apenas ViewSets (Lead, Conta, Contato, Oportunidade, Atividade, Proposta, Contrato, etc.)

### Regras:
- Manter imports no urls.py apontando para os novos arquivos
- Não alterar assinaturas de funções
- Testar cada extração isoladamente

## Frontend: pipeline/page.tsx (1308 linhas → ~400)

### Plano:
1. Extrair modal de criar oportunidade → `components/crm-vendas/modals/ModalCriarOportunidadePipeline.tsx`
2. Extrair modal de editar oportunidade → `components/crm-vendas/modals/ModalEditarOportunidade.tsx`
3. Extrair filtros do pipeline → `components/crm-vendas/PipelineFilters.tsx`

## Frontend: pdf_proposta_contrato.py (678 linhas)

### Plano:
- Extrair função base `_gerar_pdf_documento_base()` que recebe configuração
- Proposta e contrato chamam a mesma base

## Prioridade:
1. Backend views.py (alta) — risco de conflitos em edições futuras
2. Frontend pipeline (alta) — difícil de manter
3. PDF (média) — funcional mas com duplicação
