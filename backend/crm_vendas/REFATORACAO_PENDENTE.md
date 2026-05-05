# Refatoração Pendente - CRM Vendas

## Status: Backend mantido como está (funcional, risco de quebra em produção)

O `views.py` tem 2337 linhas mas está **funcional e testado em produção**. A refatoração deve ser feita em branch separada com testes.

## Backend: views.py (2337 linhas)

### Plano (fazer em branch separada):
1. **views_config.py** — Extrair: `crm_config`, `crm_config_asaas_test`, `crm_config_issnet_test`, `crm_busca`, `LoginConfigView`
2. **views_relatorios.py** — Extrair: `gerar_relatorio`, `dashboard_data`
3. **views_assinatura_publica.py** — Extrair: `AssinaturaPublicaView`, `AssinaturaPdfView`
4. **views.py** — Manter apenas ViewSets

### Por que não fazer agora:
- 2337 linhas com 74 funções interdependentes
- Sem testes automatizados para validar
- Sistema em produção com clientes ativos
- Risco de quebrar imports/referências

## Frontend: pipeline/page.tsx (1308 linhas) — FEITO parcialmente

### O que foi feito:
- Componente `ProdutoSeletorCategoria` extraído
- Componente `CrmCancelarModal` extraído
- Componente `CrmDocumentoStatusBadge` extraído

### Pendente:
- Extrair modal de criar oportunidade (~300 linhas de JSX)
- Extrair modal de editar oportunidade (~250 linhas de JSX)
- Extrair filtros do pipeline

## Boas práticas já aplicadas:
- ✅ Mixins DRY (AssinaturaDigitalMixin, VendedorFilterMixin, etc.)
- ✅ Services separados (assinatura, dashboard, google calendar)
- ✅ Componentes reutilizáveis (modais, badges, seletores)
- ✅ Isolamento multi-tenant seguro
- ✅ Cache com Redis + invalidação automática
- ✅ Constantes centralizadas (crm-constants.ts)
- ✅ Hooks customizados (useCrmLojaInfoPublica, useCrmLeadEVendedorForm)
