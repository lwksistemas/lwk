# Resumo do sistema LWK Sistemas

## Visão geral

O **LWK Sistemas** é um **SaaS multi-tenant** para gestão de lojas: um único produto atende vários tipos de negócio (clínica de estética, cabeleireiro, restaurante, CRM, e-commerce, serviços). Cada loja tem dados isolados (por schema no PostgreSQL) e um dashboard conforme o tipo de app.

---

## Como o sistema funciona

### Arquitetura

- **Frontend** (Next.js) em **Vercel** → https://lwksistemas.com.br  
- **Backend** (Django REST) em **Heroku** → API única para todas as lojas  
- **Banco**: PostgreSQL (produção) com **schemas por loja** (django-tenants) para isolamento de dados  
- **Autenticação**: JWT (tokens) entre front e API  

### Fluxos principais

1. **Acesso por loja**  
   - URL: `/loja/[slug]/login` (ex.: `/loja/clinica-vida-5889/login`).  
   - Login com usuário/senha da loja → API valida e devolve JWT.  
   - Frontend guarda token e envia no header das requisições.

2. **Multi-tenant**  
   - **Superadmin**: gerencia lojas, planos, usuários (contexto global).  
   - **Suporte**: sistema de chamados (contexto suporte).  
   - **Lojas**: cada loja usa um **schema** no PostgreSQL; a API escolhe o schema conforme o token/loja e garante que uma loja não acessa dados de outra.

3. **Tipos de app (por loja)**  
   - Cada loja tem um “tipo” (clínica estética, cabeleireiro, restaurante, CRM, e-commerce, serviços).  
   - O dashboard e as funcionalidades mudam conforme o tipo: agenda, financeiro, consultas, cardápio, etc.

4. **Integrações**  
   - **Asaas**: cobranças, assinaturas, PIX, boleto; webhooks para atualizar status.  
   - **Redis**: cache e fila (ex.: Django Q para tarefas agendadas).  

### Segurança

- Sessão única (superadmin/suporte quando aplicável).  
- Isolamento por schema (dados da loja A não acessíveis pela loja B).  
- Rate limiting nos dashboards.  
- Senha provisória com troca obrigatória quando configurado.  

---

## Linguagens e tecnologias

### Backend

| Item | Tecnologia |
|------|------------|
| **Linguagem** | **Python** |
| **Framework web / API** | **Django 4.2** + **Django REST Framework** |
| **Autenticação API** | **djangorestframework-simplejwt** (JWT) |
| **Banco de dados** | **PostgreSQL** (produção), SQLite (dev opcional) |
| **Multi-tenant** | **django-tenants** (schemas por loja) |
| **Filas / tarefas** | **Django Q** + **Redis** |
| **Documentação da API** | **drf-spectacular** (OpenAPI/Swagger) |
| **Servidor em produção** | **Gunicorn** (Heroku) |

Principais apps Django no backend: `superadmin`, `suporte`, `clinica_estetica`, `clinica_beleza`, `cabeleireiro`, `crm_vendas`, `ecommerce`, `restaurante`, `servicos`, `asaas_integration`, `notificacoes`, `push`, `whatsapp`, `rules`, `core`.

---

### Frontend

| Item | Tecnologia |
|------|------------|
| **Linguagem** | **TypeScript** |
| **Framework** | **React 19** + **Next.js 15** (App Router) |
| **Estilização** | **Tailwind CSS** |
| **Requisições à API** | **Axios** |
| **Estado (global)** | **Zustand** |
| **UI (componentes)** | **Radix UI**, **Lucide React** (ícones) |
| **Gráficos** | **Recharts** |
| **PWA** | **next-pwa** (service worker, app instalável) |
| **Build / deploy** | **Vercel** |

Ou seja: o frontend é **TypeScript + React + Next.js**, com Tailwind e o ecossistema acima.

---

## Resumo rápido

| Camada | Linguagem principal | Framework / stack |
|--------|---------------------|-------------------|
| **Backend** | **Python** | Django, DRF, PostgreSQL, Redis, Django Q |
| **Frontend** | **TypeScript** | React, Next.js, Tailwind CSS |

O sistema é um **multi-tenant SaaS**: um backend (Python/Django) e um frontend (TypeScript/Next.js) servindo várias lojas com dados isolados por schema e dashboards por tipo de app.
