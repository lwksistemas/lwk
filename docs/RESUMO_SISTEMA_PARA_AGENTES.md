# LWK Sistemas — Resumo para Agentes IA

**Atualizado em 12/10/2026**

## URLs do sistema

| Recurso | URL | Hospedagem |
|---------|-----|-----------|
| **Site público + apps** | https://lwksistemas.com.br | Magalu Cloud SP (Next.js) |
| **API REST** | https://api.lwksistemas.com.br | Magalu Cloud SP (Django) |
| **Beta (staging)** | https://beta.lwksistemas.com.br | Servidor isolado 201.54.18.213 |
| **WhatsApp API** | https://evolution.lwksistemas.com.br | Magalu Cloud SP (Evolution) |
| **Servidor de mídia** | https://media.lwksistemas.com.br | Magalu Cloud SP (Flask + Nginx) |

## Stack técnica

| Camada | Tecnologia | Detalhes |
|--------|-----------|---------|
| Backend | Django 6.1.1 + DRF 3.18.1, Gunicorn 26.2 | Magalu SP (Docker) |
| Frontend | Next.js 16.3.8, React 19.3, TypeScript 7.0.2, Tailwind 4 | Três publicações: site geral, CRM e clínica |
| Banco | PostgreSQL 18.6 (schema por loja) | Docker local |
| Cache/Filas | Redis 7.4 + django-q2 | Docker local |
| Imagens | Servidor de mídia próprio (media.lwksistemas.com.br) | Magalu SP (BV1-2-40) |
| WhatsApp | Evolution API v2.3.7 | Docker (mesmo servidor) |
| Runtime | Python 3.13 / Node.js 22 | Docker |

## Deploy

A tela da clínica e a tela do CRM publicam separadas. Login e superadmin ficam no site geral (porta 3000). CRM usa a porta 3002 (`/fe-crm`). Clínica usa a porta 3003 (`/fe-clinica`).

Correção só de código não abre o banco. Tabela ou coluna nova abre só as lojas daquele app.

```bash
# Tela geral — login e superadmin
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh frontend'

# Tela do CRM
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh frontend crm_vendas'

# Tela da clínica da beleza
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh frontend clinica_beleza'

# API — o nome do app limita migrate/ensure às lojas daquele tipo
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh backend clinica_beleza'
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh backend crm_vendas'

# Beta isolado (branch staging) — puxar o script antes de rodá-lo
ssh ubuntu@201.54.18.213 'sudo -u deploy git -C /home/deploy/lwk-beta pull --ff-only origin staging && sudo -u deploy bash /home/deploy/lwk-beta/scripts/deploy-beta-isolated.sh frontend clinica_beleza'
ssh ubuntu@201.54.18.213 'sudo -u deploy git -C /home/deploy/lwk-beta pull --ff-only origin staging && sudo -u deploy bash /home/deploy/lwk-beta/scripts/deploy-beta-isolated.sh backend crm_vendas'
```

Deploy só com esses scripts. Não use `up -d --build` sem o nome do serviço.

## O que ficou separado em 12/10/2026

- A publicação da tela do CRM não recompila a clínica, e o contrário também.
- A nota da clínica tem tela, busca de paciente e configuração próprias. A do CRM continua no CRM. A emissão usa o serviço de nota com a config do app da loja.
- A chave Asaas da clínica fica na config da clínica. A do CRM fica na config do CRM. Os avisos (webhooks) são endereços diferentes. CPF (11 dígitos) e CNPJ (14 dígitos) não reaproveitam o mesmo cliente pelo e-mail.
- A mensalidade da LWK continua na conta Asaas do superadmin.
- PDF genérico e checagem de tabela ficam no core. A clínica não empresta isso ao CRM.
- Em produção ficam a clínica da beleza e o CRM. Hotel, salão e clínica geral saíram do código. Cadastros, fotos e schemas das lojas vendidas não foram apagados.
- Um tipo de app novo nasce do zero e ganha frontend separado: container, nginx, assetPrefix e recorte de rotas. Criar o tipo no superadmin não faz isso sozinho.

Nenhum cadastro, foto ou schema foi apagado nessas mudanças.

## Arquitetura multi-tenant

- Cada loja tem schema PostgreSQL próprio (`loja_<cpf_cnpj>`)
- Models com `LojaIsolationMixin` + `LojaIsolationManager`
- TenantMiddleware resolve loja pelo token JWT
- Apps em produção: clinica_beleza e crm_vendas. O próximo tipo de app nasce do zero, com frontend separado

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
