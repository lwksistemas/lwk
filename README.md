# LWK Sistemas - Sistema Multi-Tenant SaaS

Sistema multi-tenant para clínica da beleza e CRM. Um tipo novo nasce do zero, com frontend separado.

> **Contexto completo para desenvolvimento:** [`docs/RESUMO_SISTEMA_PARA_AGENTES.md`](docs/RESUMO_SISTEMA_PARA_AGENTES.md)

## Stack Tecnológica

### Backend
- **Django 6.1** + Django REST Framework 3.18
- **PostgreSQL 18.6** (schema por loja)
- **Redis 7.4**
- **Magalu Cloud** — API, telas, banco e Evolution (`scripts/deploy-prod-magalu.sh`)

### Frontend
- **Next.js 16.3** (App Router), React 19, TypeScript, Tailwind 4
- Três publicações: site geral (login e superadmin), CRM e clínica da beleza

## Tipos de App Disponíveis

1. **Clínica da Beleza** — consultas, pacientes, profissionais, WhatsApp. Clínica de Estética usa o mesmo app.
2. **CRM Vendas** — pipeline, propostas, Asaas, NFS-e

## Configuração Local

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd backend && python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## URLs de Produção

| Serviço | URL |
|---------|-----|
| Site | https://lwksistemas.com.br |
| API | https://api.lwksistemas.com.br |
| Health | https://api.lwksistemas.com.br/api/superadmin/health |

## Documentação

- [Resumo do sistema (agentes/devs)](docs/RESUMO_SISTEMA_PARA_AGENTES.md)
- [Deploy e rollback](docs/DEPLOY_E_ROLLBACK.md)
- [Refatoração e limpeza](docs/REFATORACAO-LIMPEZA-SISTEMA.md)

## Deploy

```bash
# Produção (branch main) — tela do app corrigido
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh frontend crm_vendas'
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh frontend clinica_beleza'
ssh deploy@201.23.81.50 'cd /opt/lwk-erp && git pull --ff-only origin main && bash scripts/deploy-prod-magalu.sh backend clinica_beleza'

# Beta isolado (branch staging)
ssh ubuntu@201.54.18.213 'sudo -u deploy git -C /home/deploy/lwk-beta pull --ff-only origin staging && sudo -u deploy bash /home/deploy/lwk-beta/scripts/deploy-beta-isolated.sh frontend crm_vendas'
```

`frontend` sem nome de app publica o site geral. Detalhe em [`docs/RESUMO_SISTEMA_PARA_AGENTES.md`](docs/RESUMO_SISTEMA_PARA_AGENTES.md).

Guia: [`docs/DEPLOY_E_ROLLBACK.md`](docs/DEPLOY_E_ROLLBACK.md).

## Estrutura do Projeto

```
lwksistemas/
├── backend/              # Django
│   ├── config/           # settings, urls, db_router
│   ├── superadmin/       # gestão global
│   ├── clinica_beleza/   # app clínica beleza
│   ├── crm_vendas/       # CRM + Asaas
│   └── ...
├── frontend/             # Next.js
│   ├── app/              # App Router
│   └── lib/              # api-client, módulos por app
├── Dockerfile.magalu     # Backend
├── Dockerfile.frontend   # Frontend
└── docs/
```

## Contato

- Email: lwksistemas@gmail.com
- Site: https://lwksistemas.com.br/
