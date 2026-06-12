# LWK Sistemas - Sistema Multi-Tenant SaaS

Sistema multi-tenant completo para gestão de diferentes tipos de negócios (clínicas, CRM, hotel, etc).

> **Contexto completo para desenvolvimento:** [`docs/RESUMO_SISTEMA_PARA_AGENTES.md`](docs/RESUMO_SISTEMA_PARA_AGENTES.md)

## Stack Tecnológica

### Backend
- **Django 5** + Django REST Framework
- **PostgreSQL** (schemas por loja)
- **Redis** (cache, opcional)
- **Railway** — hospedagem backend (`lwks-backend`)

### Frontend
- **Next.js 15** (App Router)
- **TypeScript** + **Tailwind CSS**
- **Vercel** — hospedagem frontend (projeto `frontend`, Root Directory `frontend/`)

## Tipos de App Disponíveis

1. **Clínica da Beleza** — consultas, pacientes, profissionais, WhatsApp
2. **CRM Vendas** — pipeline, propostas, Asaas, NFS-e
3. **Clínica de Estética** — agendamentos e prontuários
4. **Hotel / Cabeleireiro** — módulos específicos por tipo de loja

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

## Deploy Manual (emergência)

```bash
export PATH="$HOME/.local/npm-global/bin:$PATH"

# Backend (raiz do repo)
npx railway up --service lwks-backend --detach

# Frontend (raiz do repo — Root Directory = frontend/ no painel Vercel)
npx vercel --prod --yes
```

Conta deploy: `lwksistemas@gmail.com`. Guia completo: [`docs/DEPLOY_E_ROLLBACK.md`](docs/DEPLOY_E_ROLLBACK.md).

## Estrutura do Projeto

```
lwksistemas/
├── backend/              # Django (Railway)
│   ├── config/           # settings, urls, db_router
│   ├── superadmin/       # gestão global
│   ├── clinica_beleza/   # app clínica beleza
│   ├── crm_vendas/       # CRM + Asaas
│   └── ...
├── frontend/             # Next.js (Vercel)
│   ├── app/              # App Router
│   └── lib/              # api-client, módulos por app
├── railway.toml          # release/start commands Railway
├── Dockerfile.railway
└── docs/
```

## Contato

- Email: lwksistemas@gmail.com
- Site: https://lwksistemas.com.br/
