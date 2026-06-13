# LWK Sistemas — Resumo para agentes de IA

> **Como usar este arquivo:** em um chat novo, peça ao assistente:
> *"Leia `docs/RESUMO_SISTEMA_PARA_AGENTES.md` antes de continuar."*
>
> Este documento é a fonte rápida de contexto sobre arquitetura, deploy e convenções.
> Detalhes operacionais: `docs/DEPLOY_E_ROLLBACK.md`. Convenções de código: `.kiro/steering/project-conventions.md`.

---

## 1. O que é o sistema

**LWK Sistemas** é um SaaS **multi-tenant**: uma plataforma que hospeda várias lojas (clientes), cada uma com seu tipo de negócio e banco isolado.

| Papel | URL típica | Descrição |
|-------|------------|-----------|
| **Site público + apps** | https://lwksistemas.com.br | Next.js (Vercel) |
| **API REST** | https://api.lwksistemas.com.br | Django + DRF (Railway) |
| **Superadmin** | `/superadmin/*` | Gestão global: lojas, planos, Asaas, schemas, NFS-e |
| **Loja (tenant)** | `/loja/[slug]/*` | Área do cliente (clínica, CRM, hotel…) |
| **Suporte** | `/suporte/*` | Equipe de suporte LWK |

**Repositório:** `https://github.com/lwksistemas/lwk` — branch `main`.

---

## 2. Stack

| Camada | Tecnologia | Onde roda |
|--------|------------|-----------|
| Backend | Django 5 + DRF, Gunicorn | Railway (`lwks-backend`) |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind | Vercel (projeto `frontend`, root `frontend/`) |
| Banco | PostgreSQL (schemas por loja) | Railway Postgres |
| Cache | Redis (opcional, `USE_REDIS`) | Railway |
| Arquivos | Cloudinary | Externo |
| Pagamentos | Asaas (LWK global + contas por loja no CRM) | Webhooks na API |

**Produção (jun/2026):**

- Site: `https://lwksistemas.com.br`
- API: `https://api.lwksistemas.com.br`
- Health: `GET /api/superadmin/health` → `healthy`

O README na raiz ainda menciona Heroku em alguns trechos; **produção atual é Railway + Vercel**.

---

## 3. Arquitetura multi-tenant (backend)

### 3.1 Schemas PostgreSQL

Cada loja ativa tem um **schema isolado** no mesmo Postgres:

- Schema **public** → dados globais (`superadmin`: `Loja`, `UsuarioSistema`, planos, financeiro LWK…)
- Schema **suporte** → app `suporte`
- Schema **loja_&lt;cnpj&gt;** → dados do tenant (ex.: `loja_37302743000126` para HARMONIS)

O campo `Loja.database_name` guarda o identificador (ex.: `loja_37302743000126`). O `search_path` da conexão aponta para esse schema.

### 3.2 Apps por tipo de loja

Mapeamento em `backend/superadmin/services/database_schema_service.py` → `TIPO_LOJA_EXTRA_APPS`:

| Tipo (`tipo_loja.slug`) | Apps extras no schema |
|-------------------------|------------------------|
| `clinica-beleza` | `clinica_beleza`, `whatsapp` |
| `crm-vendas` | `crm_vendas`, `nfse_integration` |
| `clinica-estetica` | `clinica_estetica` |
| `hotel` / `hotel-pousada` | `hotel` |
| `cabeleireiro` | `cabeleireiro` |
| … | ver arquivo completo |

Base comum em todo tenant: `contenttypes`, `auth`, `stores`, `products`.

### 3.3 Roteamento de banco

- `backend/config/db_router.py` — `MultiTenantRouter` direciona queries por `app_label`
- `backend/tenants/middleware.py` — `TenantMiddleware` resolve loja por URL/headers e seta thread-local
- `backend/core/mixins.py` — `LojaIsolationMixin` + `LojaIsolationManager` filtram por `loja_id`

### 3.4 Resolução de loja (crítico)

Documentação detalhada: `backend/docs/TENANT_CRM_ARCHITECTURE.md`.

Regras resumidas:

1. **Slug da loja** na URL: em geral CPF/CNPJ só dígitos (`41449198000172`)
2. Headers HTTP: **`X-Tenant-Slug` antes de `X-Loja-ID`**
3. Frontend envia ambos via `frontend/lib/api-client.ts`
4. Views devem usar `ensure_loja_context(request)` quando o middleware não bastar

### 3.5 Migrations e schemas de loja

Fluxo típico ao criar tabela nova:

1. Migration Django no app do tenant (`clinica_beleza/migrations/…`)
2. `python manage.py migrate` no **public** (registro)
3. `python manage.py migrate_all_lojas` — aplica nos schemas das lojas
4. Muitas alterações também têm comandos **`ensure_*`** idempotentes (criam tabela/coluna via SQL se migration não rodou no tenant)

Comandos `ensure_*` importantes (clínica beleza): ver `railway.toml` → `releaseCommand`.

**Auditoria de schemas (superadmin):**

- Página: `/superadmin/dashboard/schemas`
- Serviço: `backend/superadmin/services/schema_audit_service.py`
- API: `POST /api/superadmin/security-dashboard/verificar_corrigir_schemas_lojas/`
- Detecta tabelas obrigatórias faltando (`TABELAS_OBRIGATORIAS_POR_TIPO`) e, na correção, roda `migrate` + `ENSURE_COMANDOS_POR_TIPO`
- Correção em massa no front: uma requisição por loja com falha (evita timeout)

---

## 4. Autenticação

| Tipo | Login API | Área front |
|------|-----------|------------|
| Superadmin | `/api/auth/superadmin/login/` | `/superadmin/login` |
| Loja | `/api/auth/loja/login/` | `/loja/[slug]/login` |
| Suporte | `/api/auth/suporte/login/` | `/suporte/login` |

- JWT em cookies httpOnly (`USE_JWT_HTTPONLY_COOKIES`) ou tokens em `sessionStorage` (legado)
- Superadmin pode ter MFA (`superadmin/mfa_views.py`)
- `sessionStorage`: `user_type`, `loja_slug`, `current_loja_id`, etc.

---

## 5. Estrutura de pastas

```
lwksistemas/
├── backend/                    # Django (deploy: conteúdo vai para /app na imagem Docker)
│   ├── config/                 # settings, urls, wsgi, db_router
│   ├── superadmin/             # Loja, planos, financeiro LWK, dashboard segurança
│   ├── tenants/                # middleware multi-tenant
│   ├── core/                   # mixins, db_config, views_base, pagination
│   ├── clinica_beleza/         # app principal clínica beleza
│   ├── crm_vendas/             # CRM + config Asaas por loja
│   ├── hotel/, cabeleireiro/, clinica_estetica/, …
│   └── **/management/commands/ # ensure_*, migrate_all_lojas, seeds
├── frontend/
│   ├── app/                    # App Router Next.js
│   │   ├── (dashboard)/superadmin/…
│   │   ├── (dashboard)/loja/[slug]/…
│   │   └── cadastro, assinar-consentimento, etc.
│   └── lib/                    # api-client.ts, auth.ts, *-api.ts por módulo
├── railway.toml                # releaseCommand + startCommand Railway
├── Dockerfile.railway
└── docs/
```

### Frontend — rotas por módulo

- **Clínica beleza:** `/loja/[slug]/clinica-beleza/*` (consultas, pacientes, estoque, Memed, WhatsApp…)
- **CRM vendas:** `/loja/[slug]/crm-vendas/*` (pipeline, propostas, Asaas, NFS-e…)
- **Hotel:** `/loja/[slug]/hotel/*`
- **Superadmin:** `/superadmin/dashboard`, `/superadmin/lojas`, `/superadmin/asaas`, `/superadmin/dashboard/schemas`…

API base: `NEXT_PUBLIC_API_URL` → `frontend/lib/api-base.ts` → chamadas em `/api/...`.

---

## 6. Deploy

Guia completo: **`docs/DEPLOY_E_ROLLBACK.md`**.

### 6.1 Automático (recomendado)

- **Vercel:** repo `lwksistemas/lwk`, branch `main`, root `frontend/`
- **Railway:** mesmo repo, serviço `lwks-backend`, paths `backend/`, `Dockerfile.railway`, `railway.toml`
- Todo push na `main` dispara deploy; Railway executa **`releaseCommand`** (migrations + ensure + collectstatic)

### 6.2 Manual (emergência)

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /home/luiz/Documentos/lwksistemas   # raiz do monorepo

# Backend — serviço lwks-backend (NÃO evolution-api, NÃO lwks-cron)
railway up --service lwks-backend --detach

# Frontend (Vercel usa Root Directory = frontend/)
npx vercel --prod --yes
```

Conta deploy: `lwksistemas@gmail.com`.

### 6.2.1 Backend: BUILD_ID e cache Docker (CRÍTICO)

O Railway usa `Dockerfile.railway`. O Docker **reutiliza camadas em cache** se o código parecer igual.

**Sempre que mudar código do backend** (Python, migrations, fixes de produção):

1. Altere `ARG BUILD_ID=...` em `Dockerfile.railway` (valor único, ex.: hash do commit ou descrição curta).
2. Commit + `railway up --service lwks-backend --detach`.

**Redeploy** de uma imagem antiga no painel **não** aplica código novo se o BUILD_ID não mudou.

Verificar deploy real:

```bash
curl -s https://api.lwksistemas.com.br/api/superadmin/health/
# Campos úteis: "build", "status", "evolution_available"
```

### 6.2.2 Branch `main` protegida

`git push origin main` pode exigir aprovação no Cursor. Se bloquear, repetir com confirmação ou fazer deploy manual via `railway up` (código local).

### 6.3 releaseCommand (Railway)

Definido em `railway.toml` — inclui, entre outros:

- `migrate --noinput`
- `ensure_clinica_beleza_consultas`, `ensure_termo_consentimento`, `ensure_paciente_fotos_table`, …
- `migrate_all_lojas`
- `collectstatic --noinput`

**Sempre que houver migration nova**, o deploy deve passar pelo Railway (não só subir código sem release).

### 6.4 Rollback rápido

- **Vercel:** Deployments → Promote deploy anterior
- **Railway:** Redeploy do build Successful anterior
- Depois: `git revert` no repo (não force-push na `main`)

### 6.5 Checklist pós-deploy

- [ ] `GET /api/superadmin/health` → healthy
- [ ] Login superadmin (senha errada → 401, não 500)
- [ ] Uma tela de loja autenticada
- [ ] Vercel production Ready

---

## 7. Integrações importantes

### Asaas (cobrança)

- **LWK global:** webhook `/api/asaas/webhook/` + token `ASAAS_WEBHOOK_TOKEN` — assinaturas de lojas na LWK
- **CRM por loja:** conta Asaas separada, webhook `/api/crm-vendas/webhooks/asaas/[atalho]/`, token em `CRMConfig.asaas_webhook_token`
- UI CRM: `/loja/[slug]/crm-vendas/configuracoes/asaas`
- Superadmin: `/superadmin/asaas`

### NFS-e

- Emissão via integração (`nfse_integration`); superadmin em `/superadmin/nfse`

### WhatsApp

- Config por loja no **schema tenant** (`whatsapp_whatsappconfig`).
- UI: `/loja/[slug]/configuracoes/whatsapp` (todos os tipos) ou módulo clínica.
- **Meta Cloud API:** Phone ID + token + checkbox “WhatsApp ativo”.
- **WhatsApp Web (Evolution):** serviço Railway separado `evolution-api`; backend com `EVOLUTION_API_URL` + `EVOLUTION_API_KEY`.
- Colunas novas em `WhatsAppConfig` → `ensure_whatsapp_evolution_fields` (no `releaseCommand`) ou auto-fix em `whatsapp/config_service.py`.
- Doc completa: `docs/WHATSAPP_EVOLUTION.md`.
- Health expõe `evolution_available: true/false`.

### Cloudinary

- Upload de imagens no front (`frontend/components/ImageUpload.tsx`); pasta por loja: `lwksistemas/{slug}/…`

---

## 8. Convenções de desenvolvimento

### Backend

- Lógica de negócio em `*_service.py`, não em views
- `python3 manage.py check` antes de considerar pronto
- Novo app tenant: incluir em `db_router.loja_apps` + `TIPO_LOJA_EXTRA_APPS`
- Comando ensure com `--slug` para rodar em uma loja só

### Frontend

- `"use client"` em páginas interativas
- Formulários grandes → página dedicada; modais só para ações simples
- Headers de tenant centralizados em `api-client.ts`
- Diagnósticos/lint nos arquivos alterados antes de commit

### Git / commit

- Mensagens em português ou padrão `feat(modulo): …` / `fix(modulo): …`
- Commit só quando o usuário pedir
- Branch `main` pode estar protegida — push nem sempre funciona via automação; deploy manual via CLI é alternativa

---

## 9. Comandos úteis (produção / Railway)

```bash
# Shell no Railway
npx railway run python manage.py migrate_all_lojas
npx railway run python manage.py ensure_termo_consentimento --slug 37302743000126
npx railway run python manage.py auditar_schema_por_slug --slug 37302743000126

# Logs
npx railway logs
```

Local:

```bash
cd backend && python3 manage.py runserver
cd frontend && npm run dev
```

---

## 10. Lojas de referência (produção)

| Nome | Slug (CNPJ) | Tipo | Notas |
|------|-------------|------|-------|
| HARMONIS | `37302743000126` | clinica-beleza | Corrigida via auditoria de schemas (termo consentimento) |
| Clinica Nova Imagem | `novaimagem` (atalho) / CNPJ `22239255889` | clinica-beleza | db `loja_22239255889`; WhatsApp Evolution |
| Felix Representações | `41449198000172` (atalho `felix`) | crm-vendas | Conta Asaas **separada** da LWK |
| CLÍNICA VIDA | `34787081845` | clinica-beleza | |
| DR Escrita | `31682991890` | clinica-beleza | |

---

## 11. Documentos relacionados

| Arquivo | Conteúdo |
|---------|----------|
| `docs/DEPLOY_E_ROLLBACK.md` | Deploy automático, manual, rollback |
| `.kiro/steering/project-conventions.md` | Convenções para o agente no Cursor |
| `backend/docs/TENANT_CRM_ARCHITECTURE.md` | Tenant, headers, cache CRM |
| `railway.toml` | release/start commands |
| `README.md` | Visão geral (parcialmente desatualizado em URLs Heroku) |

---

## 12. Histórico recente relevante (jun/2026)

- **Auditoria de schemas:** botão "Verificar e corrigir" agora falha lojas com tabelas obrigatórias ausentes e executa `ensure_*` após migrate (`schema_audit_service.py`).
- **CRM Asaas:** páginas separadas Asaas e NFS-e; token webhook gerável por loja no CRM e no superadmin.
- **Deploy:** backend Railway (`lwks-backend`), frontend Vercel; `git push origin main` às vezes bloqueado (branch protegida) — usar `railway up` / `vercel --prod`.
- **BUILD_ID:** bump obrigatório em `Dockerfile.railway` + `railway up` para backend ir a produção de verdade.
- **Regra Cursor:** `.cursor/rules/lwk-inicio-agente.mdc` (`alwaysApply`) — cola este resumo em todo chat novo.

---

## 13. Prompt para chat novo

Cole no início de um chat se quiser reforçar:

> Leia `docs/RESUMO_SISTEMA_PARA_AGENTES.md` e `.cursor/rules/lwk-inicio-agente.mdc` antes de continuar. Produção: Vercel (front) + Railway `lwks-backend` (API). Deploy backend = bump BUILD_ID + `railway up --service lwks-backend --detach`.

---

*Última atualização: junho/2026 — manter este arquivo ao mudar arquitetura ou fluxo de deploy.*
