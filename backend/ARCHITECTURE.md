# Arquitetura do Backend LWK Sistemas

## Visão Geral

Sistema multi-tenant SaaS com um único banco PostgreSQL usando **schemas isolados** por loja.
Cada tipo de loja (CRM, Clínica, Salão, etc.) é um app Django independente com models, views e serializers próprios.

## Diagrama de Camadas

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                   │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS (JWT)
┌─────────────────────▼───────────────────────────────┐
│  config/security_middleware.py                        │
│  (CORS, Rate-limit, Isolamento por grupo)            │
├──────────────────────────────────────────────────────┤
│  tenants/middleware.py                                │
│  (Detecta tenant → configura search_path + loja_id)  │
├──────────────────────────────────────────────────────┤
│  Views (DRF ViewSets)                                │
│  ├── crm_vendas/views_*.py                           │
│  ├── clinica_estetica/views_*.py                     │
│  └── superadmin/views/                               │
├──────────────────────────────────────────────────────┤
│  core/views.py (BaseModelViewSet)                    │
│  (is_active filter, loja_id isolation, soft delete)  │
├──────────────────────────────────────────────────────┤
│  core/mixins.py (LojaIsolationManager)               │
│  (Filtra queryset por loja_id + tenant DB)           │
├──────────────────────────────────────────────────────┤
│  config/db_router.py (MultiTenantRouter)             │
│  (Direciona reads/writes para schema correto)        │
├──────────────────────────────────────────────────────┤
│  PostgreSQL (schemas: public, suporte, loja_*)       │
└──────────────────────────────────────────────────────┘
```

## Relação entre Apps

### Core (compartilhado)
- **`core/`** — Mixins, serializers base, throttling, retry, validators, email delivery
- **`config/`** — Settings, URLs, middleware de segurança, WSGI
- **`tenants/`** — Middleware de tenant, thread-local context

### Admin/Infra
- **`superadmin/`** — CRUD de lojas, planos, billing (Asaas), backup, auditoria
- **`asaas_integration/`** — Webhooks e API Asaas (boletos, PIX, cartão)
- **`nfse_integration/`** — Emissão de NFS-e (ISS.Net)

### Apps de Negócio (por tipo de loja)
| App | Tipo de Loja | Status |
|-----|-------------|--------|
| `crm_vendas/` | CRM de Vendas | ✅ Produção |
| `clinica_estetica/` | Clínica de Estética | ✅ Produção |
| `clinica_beleza/` | Clínica de Beleza / Salão | ✅ Produção |
| `cabeleireiro/` | Salão de Cabeleireiro | ✅ Produção |
| `restaurante/` | Restaurante | 🔨 Em construção |
| `hotel/` | Hotel / Pousada | 🔨 Em construção |
| `ecommerce/` | E-commerce | 🔨 Em construção |
| `servicos/` | Prestação de Serviços | 🔨 Em construção |

### `clinica_beleza` vs `clinica_estetica`
- **`clinica_beleza/`** (283 itens) — App completo para salões de beleza com agenda,
  lembretes WhatsApp, comissões, financeiro, relatórios.
- **`clinica_estetica/`** (38 itens) — App focado em clínicas de estética com
  agendamentos, consultas, evolução de pacientes, anamneses e financeiro próprio.

São **módulos distintos** para tipos de loja diferentes:
- Clínica de beleza → foco em serviços estéticos rápidos (corte, manicure)
- Clínica de estética → foco em procedimentos clínicos (protocolos, evolução)

### Comunicação
- **`whatsapp/`** — WhatsApp Cloud API (mensagens, templates, lembretes)
- **`notificacoes/`** — Notificações in-app (base)
- **`push/`** — Push notifications via VAPID

### Público
- **`homepage/`** — Página pública da loja (SEO, agendamento online)
- **`stores/`** — Listagem pública de lojas

## Padrões Arquiteturais

### 1. ViewSet Pattern (DRF)
```
BaseModelViewSet → herda → AppSpecificViewSet
                         + CRMSchemaRecoveryMixin
                         + CacheInvalidationMixin
                         + VendedorFilterMixin
```

### 2. Service Layer
Lógica complexa fica em services, não em views:
- `crm_vendas/services.py` — regras de negócio CRM
- `crm_vendas/services_financeiro.py` — cálculos financeiros
- `superadmin/backup_service/` — exportação de backup

### 3. Mixin Composition
Mixins compostos por responsabilidade:
- `LojaIsolationMixin` — isolamento de dados
- `CRMSchemaRecoveryMixin` — auto-recuperação de schema
- `CacheInvalidationMixin` — invalidação de cache
- `VendedorFilterMixin` — filtro por vendedor

### 4. Cache Strategy
- Dashboard: 60s (alta frequência, dados agregados)
- Resumo financeiro: 120s (custo alto de query)
- Invalidação: por loja_id (não global)

## Segurança

- JWT com sessão única (uma sessão ativa por usuário)
- Isolamento por grupo (admin, loja, suporte)
- Rate-limiting por endpoint (DashboardRateThrottle, ReportsThrottle)
- SQL injection prevention (quote_name + regex whitelist)
- CORS restrito por domínio
- Detector de violações de segurança em tempo real
