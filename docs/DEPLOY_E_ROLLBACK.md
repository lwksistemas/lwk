# Deploy, integração GitHub e rollback (LWK Sistemas)

Guia operacional: **homologação (beta) primeiro**, depois **produção**.

| Ambiente | Site | API | Branch Git | Railway |
|----------|------|-----|------------|---------|
| **Homologação (beta)** | https://beta.lwksistemas.com.br | https://lwks-backend-staging-staging.up.railway.app | `staging` | `lwks-backend-staging` (env **staging**) |
| **Produção** | https://lwksistemas.com.br | https://api.lwksistemas.com.br | `main` | `lwks-backend` (env **production**) |

---

## 0. Fluxo correto (sempre)

```
1. Desenvolver / corrigir no código
2. Commit + push na branch staging
3. Deploy automático (Vercel Preview + Railway staging) ou manual (seção 0.2)
4. Testar em https://beta.lwksistemas.com.br
5. Aprovar com o cliente/equipe
6. Merge staging → main
7. Deploy produção (automático via GitHub ou manual seção 1.3)
```

**Nunca** corrigir direto em `main` + `railway up --environment production` sem passar pelo beta.

### 0.1 Frontend local apontando para beta

Copie `frontend/.env.staging.local.example` → `frontend/.env.staging.local`:

```env
NEXT_PUBLIC_API_URL=https://lwks-backend-staging-staging.up.railway.app
```

### 0.2 Deploy manual homologação (beta)

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /caminho/para/lwksistemas

# Backend staging
cd backend
railway environment staging
railway up --service lwks-backend-staging --detach

# Frontend: push na branch staging dispara Preview na Vercel.
```

#### Domínio beta → branch `staging` (configuração permanente)

O beta **não** deve apontar para um deploy de **Production** (`main`). Cada push em `staging` gera um novo Preview; o domínio customizado precisa seguir a URL estável da branch:

| Domínio | Branch Git | URL estável Vercel | DNS (registro.br) |
|---------|------------|-------------------|-------------------|
| `beta.lwksistemas.com.br` | `staging` | `frontend-git-staging-lwks-projects-48afd555.vercel.app` | CNAME → `cname.vercel-dns.com` |
| `staging.lwksistemas.com.br` | `staging` | (mesma URL estável) | CNAME → `cname.vercel-dns.com` |

**Estado atual (jun/2026):** domínios configurados no Vercel + registro.br; alias apontando para a branch `staging`. Se o beta voltar a servir código de `main` (login laranja some, API errada), rode o script abaixo.

**Opção A — script (recomendado, via CLI):**

```bash
cd frontend
bash scripts/vercel-link-beta-staging.sh
```

**Opção B — painel Vercel:**

1. [Vercel → frontend → Settings → Domains](https://vercel.com/lwks-projects-48afd555/frontend/settings/domains)
2. Domínio `beta.lwksistemas.com.br` → **Edit**
3. **Connect to an environment** → **Preview** → Git Branch **`staging`**

**Opção C — alias manual (equivalente à opção A):**

```bash
cd frontend
npx vercel alias set frontend-git-staging-lwks-projects-48afd555.vercel.app beta.lwksistemas.com.br
```

**Variável de ambiente Preview (branch staging):** em Vercel → Settings → Environment Variables, para **Preview** (ou branch `staging`):

```env
NEXT_PUBLIC_API_URL=https://lwks-backend-staging-staging.up.railway.app
```

O frontend também detecta `beta.lwksistemas.com.br` em runtime (`frontend/lib/api-base.ts`).

**Verificar CSP** (deve incluir a API staging):

```bash
curl -sI https://beta.lwksistemas.com.br/superadmin/login | tr '\r' '\n' | grep connect-src
```

Verificar build da API staging:

```bash
curl -s https://lwks-backend-staging-staging.up.railway.app/api/superadmin/health/ | jq .build
```

### 0.3 Promover para produção

```bash
git checkout main
git merge staging
git push origin main
# Vercel (main) + Railway production disparam automaticamente se Git conectado
```

### 0.3.1 Obrigatório após deploy em produção — atualizar beta

Sempre que houver **push em `main`** (deploy produção), o beta **deve** receber o mesmo código:

```bash
git checkout staging
git merge main
git push origin staging
git checkout main
```

Isso dispara deploy automático em:

- **Frontend:** Vercel Preview → https://beta.lwksistemas.com.br (branch `staging`)
- **Backend:** Railway `lwks-backend-staging` (ambiente **staging**)

**Verificar beta após ~5 min:**

```bash
curl -s https://lwks-backend-staging-staging.up.railway.app/api/superadmin/health/ | jq .build
curl -sI https://beta.lwksistemas.com.br/superadmin/login | tr '\r' '\n' | grep connect-src
```

Se o site beta não refletir a branch `staging` (domínio apontando para deploy antigo):

```bash
cd frontend && bash scripts/vercel-link-beta-staging.sh
```

**Regra para agentes:** ao fazer deploy/push em produção, **sempre** executar o merge `main` → `staging` na mesma sessão, salvo instrução explícita do usuário em contrário.

> Fluxo ideal continua sendo testar no beta **antes** de merge em `main`. Quando a correção for feita direto em `main`, o passo 0.3.1 evita beta defasado.

### 0.4 Alinhar beta com produção (NFS-e e integrações)

O **código** é o mesmo após merge `staging` → `main`. O que difere entre beta e produção é o **banco de dados** e variáveis no **Railway/Vercel** — não há cópia automática.

| Item | Produção | Beta (staging) | Observação |
|------|----------|--------------|------------|
| Config NFS-e (`SuperadminNFSeConfig`) | Banco prod | Banco staging | Certificado, códigos fiscais, RPS |
| Asaas (`AsaasConfig` + env) | `$aact_prod_` | Sandbox ou prod* | Webhook URL diferente no beta |
| Webhook Asaas | `api.lwksistemas.com.br/...` | `lwks-backend-staging-.../...` | Token pode ser o mesmo ou outro |
| E-mail (Resend) | Ativo | Ativo | Mesma chave ou separada |
| **WhatsApp Web (Evolution)** | `evolution-api` + env no `lwks-backend` | **Variáveis ausentes por padrão** | Ver seção abaixo |

\*Se quiser **teste real completo no beta** (PIX + NFS-e na prefeitura), pode usar Asaas produção e ISSNet produção — entenda os riscos abaixo.

#### WhatsApp Web (Evolution) no beta

A opção **WhatsApp Web (QR)** só fica ativa quando o health da API staging retorna `evolution_available: true`:

```bash
curl -s https://lwks-backend-staging-staging.up.railway.app/api/superadmin/health/ | jq .evolution_available
```

**Produção** já tem o serviço `evolution-api`. O ambiente **staging** não copia isso automaticamente.

**Opção A — teste rápido (compartilhar Evolution de produção):**

No Railway → ambiente **staging** → serviço **`lwks-backend-staging`** → **Variables**, adicione (copie os mesmos valores de `lwks-backend` em **production**):

```env
EVOLUTION_API_URL=https://evolution-api-production-....up.railway.app
EVOLUTION_API_KEY=<mesma AUTHENTICATION_API_KEY da Evolution prod>
API_BASE_URL=https://lwks-backend-staging-staging.up.railway.app
```

Redeploy do `lwks-backend-staging`. Cada loja no beta usa instância `lwk_loja_{id}` (ID do banco staging — não conflita com produção se o ID for diferente).

**Opção B — Evolution dedicada no staging:** subir `evolution-api` no ambiente staging (Postgres + Redis próprios). Ver `docs/WHATSAPP_EVOLUTION.md`.

Depois do redeploy, confirme `evolution_available: true` e recarregue https://beta.lwksistemas.com.br/loja/sorriso/configuracoes/whatsapp .

#### Checklist manual (Superadmin → NFS-e config no beta)

Replicar os mesmos valores de produção em https://beta.lwksistemas.com.br/superadmin/nfse-config:

1. **Provedor:** ISSNet (Municipal)
2. **Emitir automaticamente:** ligado
3. **Prestador:** CNPJ, razão social, IM, e-mail (iguais à prod)
4. **Credenciais ISSNet:** usuário, senha WS, certificado `.pfx`, senha do certificado
5. **Ambiente ISSNet:** Produção (se teste real)
6. **Dados fiscais:**
   - Item LC 116: `14.01`
   - **Código tributação municipal:** `140118` (obrigatório — não deixar vazio)
   - Código serviço legado: `140118`
   - CNAE: `9511800`
7. **Último RPS:** copiar de produção **ou** manter contador próprio no beta (`--keep-counters` no import)

#### Sincronizar via comando (produção → beta)

```bash
# 1) Exportar na produção (Railway SSH no lwks-backend)
python manage.py nfse_config_sync export -o /tmp/nfse_config.json

# 2) Copiar arquivo para máquina local / staging

# 3) Importar no beta (Railway SSH no lwks-backend-staging)
python manage.py nfse_config_sync import -i /tmp/nfse_config.json --keep-counters
```

`--keep-counters` evita que o beta sobrescreva `ultimo_rps` de produção; use se **ambos** emitirem NFS-e real.

#### Asaas no beta (cadastro + PIX de teste real)

1. Railway **staging** → variáveis `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN` (produção ou sandbox)
2. Superadmin → Asaas no beta: mesma chave e webhook token
3. Webhook no painel Asaas apontando para:
   `https://lwks-backend-staging-staging.up.railway.app/api/asaas/webhook/`

#### Atenção — emissão real no beta

- ISSNet **produção** no beta gera **nota fiscal real** na prefeitura (mesmo CNPJ/IM).
- Cada emissão consome **número de RPS** — mantenha `ultimo_rps` sincronizado ou use `--keep-counters` e atualize manualmente após testes.
- Para testes frequentes de NFS-e, prefira **produção** com lojas de teste ou **homologação ISSNet** (se o município oferecer).

---

## 1. Produção — deploy automático via GitHub (nativo)

**Não usar GitHub Actions com `railway up` / `vercel` como padrão.** Conectar o repositório em cada plataforma — menos manutenção e o Railway executa o `releaseCommand` (migrations) em todo deploy.

Repositório: `https://github.com/lwksistemas/lwk` — branch **`main`**.

### 1.1 Vercel (frontend)

1. [Vercel Dashboard](https://vercel.com) → projeto **frontend**.
2. **Settings** → **Git** → conectar repositório `lwksistemas/lwk`.
3. **Root Directory:** `frontend` (obrigatório — monorepo com código em `frontend/`)
4. **Production Branch:** `main`
5. **Require Verified Commits:** **desligado** — commits via Cursor/CLI chegam como *unverified* no GitHub; com essa opção ativa a Vercel **cancela** o deploy (status `CANCELED`, motivo *unverified commit*).
6. (Opcional) **Ignored Build Step:** só buildar se mudou algo em `frontend/` — use caminho `.` (não `frontend/`), pois o comando roda **dentro** do Root Directory:

```bash
git diff HEAD^ HEAD --quiet -- .
```

Cada push na `main` que altera o front gera deploy de produção. PRs podem gerar **Preview** para testar antes.

**Erro comum — deploy cancelado (0 ms, sem build):**

| Sintoma | Causa | Correção |
|---------|--------|----------|
| Status `CANCELED`, *unverified commit* | **Require Verified Commits** ativo | Vercel → Settings → Git → desmarcar *Require Verified Commits* |
| Status `CANCELED`, build ignorado | *Ignored Build Step* com path errado (`frontend/` em vez de `.`) | Ajustar script ou remover ignore step |
| Root Directory vazio | Build aponta para raiz do repo (sem `package.json`) | Definir Root Directory = `frontend` |

### 1.2 Railway (backend)

1. [Railway](https://railway.com) → projeto **refreshing-contentment** → serviço **lwks-backend**.
2. **Settings** → **Source** → **Connect GitHub** → repo `lwksistemas/lwk`, branch `main`.
3. **Wait for CI:** deixe **desligado** até o workflow `Security` passar no GitHub; com CI falhando, deploys são **SKIPPED**. Depois que `pip-audit` e `npm audit` passarem, pode ligar.
4. (Opcional) **Watch paths:** `backend/`, `Dockerfile.railway`, `railway.toml` — definidos em **`railway.toml`** → `[build].watchPatterns` (vale para `lwks-backend` e `lwks-backend-staging`, que usam o mesmo repo).

**Beta:** serviço `lwks-backend-staging`, branch `staging`, mesmas regras de Wait for CI e watch paths.

**⚠️ Nunca duplicar serviços entre ambientes Railway:**

| Serviço | Ambiente correto | Branch | Nunca colocar em |
|---------|------------------|--------|------------------|
| `lwks-backend` | **production** | `main` | staging |
| `lwks-backend-staging` | **staging** | `staging` | **production** |
| `evolution-api` | **production** | — | staging (opcional separado) |
| `lwks-cron` | **production** | — | staging |

Se `lwks-backend-staging` aparecer em production com healthcheck FAILED, remova só desse ambiente:

```bash
railway environment production
railway service delete --service lwks-backend-staging --environment production --yes
```

**Auto-deploy lento ou “não disparou”:**

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| Push na `main` sem deploy em ~1 min | Atraso normal do webhook Railway | Aguardar **5–10 min**; no histórico, **Show Skipped** |
| Deploy **SKIPPED** | **Wait for CI** ligado + workflow `Security` falhou | Corrigir deps ou desligar Wait for CI |
| Só `railway up` funciona | Repo não conectado ou branch errada | `railway service source connect --repo lwksistemas/lwk --branch main --service lwks-backend` |
| Prompt “external contributor” | Commit com co-autor fora do time Railway | Evitar `Co-authored-by:` de agentes; ou aprovar no painel |

O `railway.toml` já define `releaseCommand` (`migrate` → `migrate_all_lojas` → `ensure_all`) — **sempre rode deploy pelo Railway após mudanças de migration**, nunca só subir código sem release.

### 1.2.2 Railway — serviço `lwks-worker` (fila assíncrona)

Processa tarefas em background via **django-q + Redis** (WhatsApp, retry de assinatura, e-mails, NFS-e).

| Serviço | Comando | Quando usar |
|---------|---------|-------------|
| `lwks-backend` | Gunicorn | API HTTP — **sem** schedulers WSGI (padrão) |
| `lwks-cron` | `executar_cron_lwks` a cada 15 min | Lembretes, backups, NFS-e retry, segurança |
| `lwks-worker` | `python manage.py qcluster` | Fila assíncrona on-demand |

**Variáveis** (copiar referências de `lwks-backend`):

```env
SECRET_KEY=${{lwks-backend.SECRET_KEY}}
DATABASE_URL=${{lwks-backend.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
USE_REDIS=true
USE_TASK_QUEUE=false
LWK_PROCESS_ROLE=worker
DJANGO_SETTINGS_MODULE=config.settings_production
LWK_SKIP_STARTUP_ENSURE=1
RAILWAY_CONFIG_FILE=railway.worker.toml
```

**Importante:** `USE_TASK_QUEUE=false` no **lwks-worker** (só enfileira no `lwks-backend`). Mesmo assim o worker **precisa** de `REDIS_URL` — consome a fila Redis via `Q_CLUSTER` (não re-enfileira tarefas).

No painel Railway → **lwks-worker** → Settings → desativar **Healthcheck** (qcluster não serve HTTP).

Deploy manual:

```bash
railway up --service lwks-worker -c railway.worker.toml --detach
```

Health da API expõe `task_queue` com monitoramento da fila:

```json
"task_queue": {
  "enabled": true,
  "broker": "redis",
  "role": "web",
  "queued": 0,
  "workers_alive": 4,
  "clusters": 1,
  "failures_24h": 0,
  "health": "degraded"
}
```

| Campo | Significado |
|-------|-------------|
| `queued` | Tarefas aguardando no Redis |
| `workers_alive` | Workers django-q ativos (heartbeat ~3s) |
| `failures_24h` | Falhas registradas nas últimas 24h |
| `health` | `degraded` se fila > 50; `unhealthy` se fila > 200 (HTTP 503). `workers_alive=0` com fila > 0 também degrada. |

Limites configuráveis: `LWK_QUEUE_BACKLOG_DEGRADED` (padrão 50), `LWK_QUEUE_BACKLOG_UNHEALTHY` (padrão 200).

Com worker ativo: `enabled: true`, `broker: redis`, `workers_alive` ≥ 1.

**Schedulers WSGI desativados por padrão** — o Gunicorn não roda mais threads de WhatsApp/backup em paralelo com o cron. Tarefas periódicas ficam só no `lwks-cron`.

**Fila assíncrona (django-q):**

| Tipo | Enfileira em | Executa em |
|------|--------------|------------|
| WhatsApp (`send_whatsapp`) | `lwks-backend` | `lwks-worker` |
| E-mail (`send_prepared`, `send_system_mail`, `msg.send()` via Resend) | `lwks-backend` | `lwks-worker` |
| NFS-e (assinatura, loja, manual, comissão) | `lwks-backend` | `lwks-worker` |
| Webhooks Asaas (global LWK + por loja CRM) | `lwks-backend` | `lwks-worker` |
| Webhook Mercado Pago (mensalidade LWK) | `lwks-backend` | `lwks-worker` |
| CRM — enviar proposta/contrato (PDF + email/WhatsApp) | `lwks-backend` | `lwks-worker` |
| Cron (lembretes, backups, retry NFS-e) | — (síncrono no `lwks-cron`) | `lwks-cron` |

E-mails com anexo > 4 MB são enviados de forma síncrona (ex.: backup por email no cron).

### 1.2.1 Railway — serviço `lwks-cron` (backups automáticos)

Serviço **cron** separado (`railway.cron.toml`): roda `python manage.py executar_cron_lwks` **a cada 15 minutos** (`*/15 * * * *`):

- Lembretes WhatsApp de **atividades CRM** (24h e 2h antes, campos `lembrete_whatsapp*` no banco da loja)
- Lembretes WhatsApp de **agendamentos clínica**
- **Backups** automáticos por email (no minuto `:00`)

**Erro comum:** deploy/cron falha com `ValueError: SECRET_KEY deve estar configurada` — o `lwks-cron` **não herda** variáveis do `lwks-backend` automaticamente.

No painel Railway → **lwks-cron** → **Variables**, adicione referências ao backend (exemplo):

```env
SECRET_KEY=${{lwks-backend.SECRET_KEY}}
ALLOWED_HOSTS=${{lwks-backend.ALLOWED_HOSTS}}
DATABASE_URL=${{lwks-backend.DATABASE_URL}}
DJANGO_SETTINGS_MODULE=config.settings_production
RESEND_API_KEY=${{lwks-backend.RESEND_API_KEY}}
DEFAULT_FROM_EMAIL=${{lwks-backend.DEFAULT_FROM_EMAIL}}
FIELD_ENCRYPTION_KEY=${{lwks-backend.FIELD_ENCRYPTION_KEY}}
```

Deploy manual do cron (se necessário):

```bash
railway up --service lwks-cron -c railway.cron.toml
```

**Não** faça `railway up` no serviço `lwks-cron` com `evolution-api` ou `lwks-backend` linkado por engano.

### 1.3 Deploy manual (emergência / quando Git não dispara)

CLIs (PATH local típico: `~/.local/npm-global/bin`):

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"

# Backend (raiz do repo)
cd /caminho/para/lwksistemas
npx railway up --service lwks-backend --detach

# Frontend (raiz do repo — Root Directory = frontend/ no painel Vercel)
npx vercel --prod --yes
```

Login: `railway whoami`, `vercel whoami` (conta `lwksistemas@gmail.com`).

---

## 2. Rollback em ~2 minutos (atualização bugada)

**PDF para download:** [manual-rollback-emergencia-lwk.pdf](https://lwksistemas.com.br/docs/manual-rollback-emergencia-lwk.pdf)  
Gerar novamente: `python docs/scripts/gerar_manual_rollback_emergencia_pdf.py`

**Ordem:** estabilizar produção primeiro (rollback nas plataformas), corrigir no Git depois.

### 2.1 Frontend — Vercel (mais rápido)

**Painel**

1. [Vercel → frontend → Deployments](https://vercel.com/lwks-projects-48afd555/frontend)
2. Localize o deploy **Ready** **anterior** ao bugado (data/hora + mensagem de commit).
3. **⋯** → **Promote to Production** (ou **Rollback**).

**CLI**

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /caminho/para/lwksistemas
vercel ls                    # lista deploys recentes
vercel promote <URL_DO_DEPLOY_BOM> --prod
```

> **Nota:** o deploy manual deve ser feito da **raiz do repo** (não de `frontend/`), pois o projeto Vercel usa Root Directory = `frontend/`.

**Verificar:** https://lwksistemas.com.br/superadmin/login → deve abrir (HTTP 200).

---

### 2.2 Backend — Railway

**Painel**

1. [Railway → lwks-backend → Deployments](https://railway.com/project/3c0f435b-964f-4612-8dc1-c05a61a8d685/service/ccfb38c6-c340-476d-a414-0404ed9afb85)
2. Deploy **Successful** imediatamente **antes** do deploy ruim.
3. **Redeploy** / reativar esse deployment (rollback para a imagem daquele build).

**CLI** (versões do CLI podem variar):

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"
cd /caminho/para/lwksistemas
railway status
railway deployment list
# Redeploy do deployment ID bom pelo painel se o CLI não expuser rollback direto
```

**Verificar:**

```bash
curl -s https://api.lwksistemas.com.br/api/superadmin/health
# Esperado: "status": "healthy", "database": "connected"
```

Login (credencial inválida deve dar **401**, nunca **500**):

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  https://api.lwksistemas.com.br/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"x"}'
```

---

### 2.3 Rollback dos dois ao mesmo tempo

| Passo | Ação | Tempo |
|-------|------|-------|
| 1 | Promote deploy anterior na **Vercel** | ~30 s |
| 2 | Redeploy deploy anterior no **Railway** | ~1–3 min |
| 3 | Testar login superadmin + uma tela de loja | ~1 min |

Se o bug for **só no front** ou **só na API**, pode reverter só um lado. Se mudou contrato API + front juntos, reverta **os dois** para o mesmo “momento” (deploys do mesmo dia/commit).

---

## 3. Depois do rollback: corrigir no Git

Rollback na plataforma **não substitui** corrigir o código no repositório.

```bash
# Ver últimos commits
git log --oneline -5

# Reverter commit ruim (cria commit novo, seguro para main)
git revert <hash_do_commit_ruim> --no-edit
git push origin main
```

- **Evitar** `git reset --hard` + `force push` na `main` em produção.
- Após o fix, um novo push dispara deploy automático (se GitHub estiver conectado) ou use deploy manual.

---

## 4. O que o rollback NÃO desfaz

| Situação | Rollback de código |
|----------|-------------------|
| Bug só em Python/TypeScript | ✅ Resolve |
| Bug só em UI | ✅ Resolve (Vercel) |
| Migration **aditiva** já aplicada (ex.: coluna nova) | ⚠️ App antigo costuma funcionar; app novo quebra se voltar sem coluna |
| Migration **destrutiva** ou dados apagados | ❌ Precisa **restore de backup** do Postgres (Railway → Database → Backups) |

**Regra:** preferir migrations que só **adicionam** colunas/tabelas; evitar `DROP` em produção sem backup e plano de restore.

---

## 5. Checklist pós-deploy (evitar incidente tipo MFA 500)

Antes de considerar deploy “ok”:

- [ ] Railway: release terminou sem erro (`migrate` no log do deploy).
- [ ] `GET /api/superadmin/health` → `healthy`.
- [ ] Login superadmin com senha errada → **401** (não 500).
- [ ] Login real superadmin (se possível) → **200**.
- [ ] Uma rota de loja autenticada (ex.: clínica-beleza) → não 500.
- [ ] Vercel: deploy **Ready** em produção.
- [ ] Página `/superadmin/login` → 200.

---

## 6. Referências no projeto

| Arquivo | Conteúdo |
|---------|----------|
| `railway.toml` | `releaseCommand`: migrate → migrate suporte → **migrate_all_lojas** → ensure_all → collectstatic |
| `Dockerfile.railway` | Build da API |
| `frontend/.env.railway.example` | `NEXT_PUBLIC_API_URL` |
| `backend/.env.example` | Webhooks, MFA, cookies httpOnly |
| `docs/scripts/gerar_resumo_melhorias_2026_pdf.py` | PDF resumo das melhorias (geração local) |

---

## 7. Resumo em uma frase

**Deploy automático:** GitHub → Vercel (`frontend/`) + Railway (`lwks-backend`).  
**Bug em produção:** Promote/Rollback na Vercel + redeploy do deployment bom no Railway → depois `git revert` e novo deploy quando estiver corrigido.

*Última atualização: junho/2026 — alinhado ao projeto refreshing-contentment / lwks-backend.*
