# Análise e otimizações – Clínica da Beleza

Sistema completo para gestão de clínicas de estética e beleza: agendamentos, procedimentos, pacientes e pagamentos.

## O que foi feito

### 1. Backend – menos duplicação e código mais direto

- **Helper de WhatsApp**  
  Criada a função `_get_whatsapp_config_for_loja(loja_id=None, request=None)` em `backend/clinica_beleza/views.py`.  
  Ela centraliza a obtenção de `(config, loja)` para envio de confirmação/lembrete WhatsApp e fallback por headers `X-Loja-ID` / `X-Tenant-Slug`.  
  Uso unificado em:
  - `AgendaUpdateView` (status CONFIRMED)
  - `AgendaCreateView` (confirmação ao criar)
  - `EnviarConfirmacaoView` (reenvio manual)
  - `CampanhaPromocaoEnviarView` (envio em massa)

- **Menos imports e blocos repetidos**  
  Remoção de blocos repetidos de `get_current_loja_id` + `Loja` + `WhatsAppConfig` nas views acima.

### 2. Frontend – headers de tenant em um só lugar

- **`getClinicaBelezaHeadersWithLoja(loja?)`** em `frontend/lib/clinica-beleza-api.ts`  
  Única função que monta os headers com auth + tenant (X-Loja-ID ou X-Tenant-Slug), com fallback para `sessionStorage` e slug da URL.

- **Dashboard**  
  O template do dashboard Clínica da Beleza passou a usar `getClinicaBelezaHeadersWithLoja(loja)` em vez de duplicar a lógica em `getHeadersComTenant()`.

### 3. Scripts na raiz do backend

Scripts em `backend/` que parecem de **teste, debug ou setup pontual**. Podem ser movidos para algo como `backend/scripts/legacy/` ou mantidos só para uso manual/documentado:

| Script | Uso provável | Sugestão |
|--------|----------------|----------|
| `force_load_clinica_beleza.py` | Teste de carga do app | Mover para `scripts/legacy` ou remover |
| `test_app_loading.py` | Teste | Mover para `scripts/legacy` ou `tests/` |
| `debug_installed_apps.py` | Debug | Mover para `scripts/legacy` |
| `test_clinica_beleza_import.py` | Teste de import | Mover para `scripts/legacy` ou `tests/` |
| `create_clinica_beleza_tables.py` | Criação de tabelas (provisioning) | Manter ou mover para `scripts/` |
| `apply_clinica_beleza_migrations.py` | Aplicar migrations | Manter ou usar `manage.py migrate` |
| `fix_clinica_beleza_schema.py` | Correção de schema | Manter em `scripts/` se ainda usado |
| `popular_loja_clinica_beleza.py` | Popular dados de teste | Manter em `scripts/` |
| `verificar_clinica_beleza_producao.py` | Verificação em produção | Manter em `scripts/` |
| `limpar_dados_clinica_beleza.py` | Limpeza de dados | Manter em `scripts/` |
| `setup_clinica_beleza_producao.py` | Setup de produção | Manter em `scripts/` |
| `criar_planos_clinica_beleza.py` | Criação de planos | Manter em `scripts/` |
| `criar_tipo_loja_clinica_beleza.py` | Criação de tipo de loja | Manter em `scripts/` |
| `criar_dados_clinica_beleza.py` | Criação de dados iniciais | Manter em `scripts/` |

Não foram removidos automaticamente para evitar quebra de fluxos de provisionamento ou verificação. Recomenda-se mover apenas os claramente de teste/debug (`test_*`, `debug_*`, `force_load_*`) para `backend/scripts/legacy/` e referenciar este doc.

## Dicas de desempenho

- **Listagens**  
  As list views já usam `select_related` onde há FKs (agendamentos, pagamentos). Pacientes, profissionais e procedimentos não têm FKs na listagem, então não há ganho extra com `select_related` ali.

- **Dashboard**  
  O endpoint `/clinica-beleza/dashboard/` já retorna estatísticas e próximos agendamentos em uma única resposta. Se no futuro for necessário reduzir mais latência, pode-se avaliar cache (ex.: Redis) para o resumo do dia.

- **Tenant**  
  Garantir que o frontend sempre envie `X-Loja-ID` ou `X-Tenant-Slug` (via `getClinicaBelezaHeadersWithLoja`) evita 404 “Contexto de loja não encontrado” e reprocessamento desnecessário no backend.

## Estrutura principal

- **Backend:** `backend/clinica_beleza/` (models, views, serializers, urls, permissions).
- **Frontend:** `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/` (pacientes, profissionais, procedimentos, campanhas, financeiro) e dashboard em `dashboard/templates/clinica-beleza.tsx`.
- **API cliente:** `frontend/lib/clinica-beleza-api.ts` (base URL, headers com tenant, fetch com tratamento de 401 e report de erros ao suporte).
- **Offline:** `frontend/lib/offline-db.ts` e `offline-sync.ts` (IndexedDB e fila de sincronização para pacientes, profissionais, procedimentos, agendamentos).
