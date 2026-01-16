# Sistema Multi-Loja - Django + Next.js 15

Sistema completo de multi-loja com isolamento total de tenants, autenticação JWT e arquitetura moderna.

## 🏗️ Arquitetura

### Backend (Django)
- **Multi-tenancy**: Isolamento completo por loja usando django-tenant-schemas
- **API REST**: Django REST Framework com autenticação JWT
- **Segurança**: Query-level filtering e permissões por usuário
- **Deploy**: Otimizado para Heroku/Render com Gunicorn + WhiteNoise

### Frontend (Next.js 15)
- **App Router**: Rotas modernas com Server/Client Components
- **Isolamento**: Middleware para tenant isolation
- **State**: Zustand para gerenciamento de estado global
- **UI**: Tailwind CSS + Shadcn/ui components
- **Type-safe**: TypeScript end-to-end

## 🚀 Setup Rápido

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Criar banco de dados PostgreSQL
createdb multistore_db

# Migrations
python manage.py migrate_schemas --shared
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Rodar servidor
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.local.example .env.local

# Rodar em desenvolvimento
npm run dev
```

Acesse:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin Django: http://localhost:8000/admin

## 📁 Estrutura do Projeto

```
multi-store-system/
├── backend/
│   ├── config/              # Configurações Django
│   ├── tenants/             # App de multi-tenancy
│   ├── stores/              # App de lojas
│   ├── products/            # App de produtos
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/
    ├── app/
    │   ├── (auth)/          # Rotas de autenticação
    │   ├── (dashboard)/     # Rotas protegidas
    │   ├── layout.tsx
    │   └── page.tsx
    ├── components/
    │   └── tenant/          # Componentes de tenant
    ├── lib/
    │   ├── api-client.ts    # Axios com interceptors
    │   ├── auth.ts          # JWT handling
    │   └── tenant.ts        # Tenant context
    ├── hooks/
    │   └── use-tenant.ts    # Hook de isolamento
    └── middleware.ts        # Proteção de rotas
```

## 🔐 Segurança

### Backend
- ✅ JWT com refresh token automático
- ✅ Query-level filtering por usuário
- ✅ Permissões granulares no ViewSet
- ✅ CORS configurado
- ✅ Isolamento de schema por tenant

### Frontend
- ✅ Middleware de autenticação
- ✅ Interceptors para refresh token
- ✅ Context de tenant isolado
- ✅ Type-safe com TypeScript
- ✅ Proteção de rotas sensíveis

## 🌐 Deploy

### Heroku (Backend)

```bash
# Login
heroku login

# Criar app
heroku create seu-app-backend

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:mini

# Configurar variáveis
heroku config:set SECRET_KEY=sua-chave-secreta
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=seu-app-backend.herokuapp.com

# Deploy
git push heroku main
```

### Render (Frontend)

1. Conecte seu repositório no Render
2. Configure:
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm start`
   - Environment: `NEXT_PUBLIC_API_URL=https://seu-backend.herokuapp.com`

## 📊 Modelos de Dados

### Tenant
- Schema isolado por loja
- Domínios customizados

### Store
- Pertence a um usuário (owner)
- Slug único
- Logo e descrição

### Product
- Pertence a uma Store
- Preço, estoque, imagem
- Slug único por loja

## 🔧 Funcionalidades

- ✅ Autenticação JWT com refresh automático
- ✅ Multi-tenancy com isolamento total
- ✅ CRUD de lojas e produtos
- ✅ Dashboard com métricas
- ✅ Seletor de loja no frontend
- ✅ Filtros por tenant
- ✅ API RESTful completa
- ✅ TypeScript end-to-end
- ✅ Responsivo (mobile-first)

## 🛠️ Tecnologias

**Backend:**
- Django 5.0
- Django REST Framework
- SimpleJWT
- django-tenant-schemas
- PostgreSQL
- Gunicorn + WhiteNoise

**Frontend:**
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Zustand
- Axios

## 📝 Próximos Passos

- [ ] Adicionar testes unitários
- [ ] Implementar upload de imagens
- [ ] Sistema de pedidos
- [ ] Relatórios e analytics
- [ ] Webhooks para integrações
- [ ] Multi-idioma (i18n)
- [ ] Dark mode
- [ ] PWA support

## 📄 Licença

MIT
