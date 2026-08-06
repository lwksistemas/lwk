# LWK Sistemas — Resumo para Agentes IA

**Atualizado em 06/08/2026**

## URLs do sistema

| Recurso | URL | Hospedagem |
|---------|-----|-----------|
| **Site público + apps** | https://lwksistemas.com.br | Magalu Cloud SP (Next.js) |
| **API REST** | https://api.lwksistemas.com.br | Magalu Cloud SP (Django) |
| **Beta (staging)** | https://beta.lwksistemas.com.br | Magalu Cloud SP (Next.js :3001) |
| **WhatsApp API** | https://evolution.lwksistemas.com.br | Magalu Cloud SP (Evolution) |
| **Servidor de mídia** | https://media.lwksistemas.com.br | Magalu Cloud SP (Flask + Nginx) |

## Stack técnica

| Camada | Tecnologia | Detalhes |
|--------|-----------|---------|
| Backend | Django 6.0.8 + DRF 3.17.1, Gunicorn | Magalu SP (Docker) |
| Frontend | Next.js 16.2.10 (App Router), TypeScript 7.0.2, Tailwind 4 | Magalu SP (Docker standalone) |
| Banco | PostgreSQL 18 (schemas por loja) | Docker local |
| Cache/Filas | Redis 7.4 + django-q2 | Docker local |
| Imagens | Servidor de mídia próprio (media.lwksistemas.com.br) | Magalu SP (BV1-2-40) |
| WhatsApp | Evolution API v2.3.7 | Docker (mesmo servidor) |
| Runtime | Python 3.13 / Node.js 22 | Docker |

## Deploy

```bash
# Produção (branch main)
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull && docker compose -f docker-compose.prod.yml up -d --build'

# Beta (branch staging)
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && ./deploy-beta.sh'

# Só backend (após mudanças Python)
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull && docker compose -f docker-compose.prod.yml up -d --build backend worker'

# Só frontend (após mudanças JS/TS)
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull && docker compose -f docker-compose.prod.yml up -d --build frontend'

# Migrations
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && docker compose -f docker-compose.prod.yml exec backend python manage.py migrate'
```

**NÃO usar:** `npx railway up`, `npx vercel`, `heroku` — serviços descontinuados.

## Arquitetura multi-tenant

- Cada loja tem schema PostgreSQL próprio (`loja_<cpf_cnpj>`)
- Models com `LojaIsolationMixin` + `LojaIsolationManager`
- TenantMiddleware resolve loja pelo token JWT
- Apps por tipo: clinica_beleza, crm_vendas, cabeleireiro, hotel

## Estrutura principal

```
lwksistemas/
├── backend/                    # Django
│   ├── config/                 # Settings, URLs
│   ├── core/                   # Mixins, utils, media_storage.py
│   ├── superadmin/             # Lojas, usuários, planos
│   ├── clinica_beleza/         # App clínica
│   ├── crm_vendas/             # CRM
│   ├── asaas_integration/      # Financeiro
│   ├── nfse_integration/       # NFS-e
│   └── whatsapp/               # WhatsApp
├── frontend/                   # Next.js 16
│   ├── app/(dashboard)/        # Páginas autenticadas
│   ├── components/             # Componentes React
│   └── lib/                    # API client, utils
├── docker-compose.prod.yml     # Compose produção
├── Dockerfile.magalu           # Backend (Python 3.13)
├── Dockerfile.frontend         # Frontend (Node 22 standalone)
├── deploy.sh                   # Deploy produção
├── deploy-beta.sh              # Deploy beta
└── backup.sh                   # Backup Postgres
```

## Padrões de código

- **Backend**: Views com APIView + GetObjectMixin; lógica em `*_service.py`
- **Frontend**: `"use client"` em páginas interativas; formulários grandes em página dedicada
- **Commits**: `feat(modulo):`, `fix(modulo):`, `refactor(modulo):`

## Servidores

| Servidor | IP | Specs | Função |
|----------|-----|-------|--------|
| lwksistemas | 201.23.81.50 | 8vCPU, 16GB, 150GB | Sistema completo |
| lwk-media | 201.23.87.251 | 1vCPU, 2GB, 40GB | Armazenamento imagens |

## Verificação rápida

```bash
# Health check
curl https://api.lwksistemas.com.br/api/superadmin/health/

# Logs
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && docker compose -f docker-compose.prod.yml logs --tail=50'
```
