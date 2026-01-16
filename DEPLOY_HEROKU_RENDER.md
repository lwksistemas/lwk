# 🚀 Deploy para Heroku e Render - Modo SINGLE DATABASE

## 📊 Arquitetura de Deploy

O sistema foi otimizado para usar **SINGLE DATABASE** em produção:

```
┌─────────────────────────────────────────────────────┐
│         PRODUÇÃO (Heroku/Render)                    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │     PostgreSQL (SINGLE DATABASE)            │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │  Tabela: stores                       │  │    │
│  │  │  - tenant_slug (index)                │  │    │
│  │  │  - access_type (superadmin/suporte)   │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │  Tabela: products                     │  │    │
│  │  │  - tenant_slug (index)                │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                              │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │  Tabela: suporte_chamado              │  │    │
│  │  │  - loja_slug (referência)             │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                              │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Vantagens do Modo SINGLE:

✅ **Compatível com Heroku/Render** - Um único banco PostgreSQL  
✅ **Mais barato** - Não precisa de múltiplos bancos  
✅ **Mais simples** - Gerenciamento facilitado  
✅ **Backups unificados** - Um backup para tudo  
✅ **Queries cross-tenant** - Relatórios consolidados  
✅ **Escalável** - PostgreSQL aguenta milhões de registros  

---

## 🔧 Configuração para Deploy

### 1. Preparar Arquivos

O sistema já está preparado com:
- ✅ `Procfile` - Comandos para Heroku
- ✅ `runtime.txt` - Versão do Python
- ✅ `requirements.txt` - Dependências
- ✅ `settings_single_db.py` - Config para produção

### 2. Variáveis de Ambiente

Configure estas variáveis no Heroku/Render:

```bash
# Obrigatórias
SECRET_KEY=sua-chave-secreta-super-segura-aqui
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Auto no Heroku
ALLOWED_HOSTS=seu-app.herokuapp.com,seu-app.onrender.com

# Opcionais
DEBUG=False
CORS_ORIGINS=https://seu-frontend.vercel.app
```

---

## 🚀 Deploy no Heroku

### Passo 1: Instalar Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh

# Windows
# Baixe de: https://devcenter.heroku.com/articles/heroku-cli
```

### Passo 2: Login e Criar App

```bash
# Login
heroku login

# Criar app
heroku create seu-app-multistore

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:mini
```

### Passo 3: Configurar Variáveis

```bash
# Secret Key (gere uma nova)
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Hosts
heroku config:set ALLOWED_HOSTS=seu-app-multistore.herokuapp.com

# CORS (se frontend separado)
heroku config:set CORS_ORIGINS=https://seu-frontend.vercel.app

# Usar settings de produção
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_single_db
```

### Passo 4: Deploy

```bash
# Adicionar remote do Heroku
heroku git:remote -a seu-app-multistore

# Deploy
git push heroku main

# Rodar migrations
heroku run python backend/manage.py migrate

# Criar superusuário
heroku run python backend/manage.py createsuperuser

# Ver logs
heroku logs --tail
```

### Passo 5: Configurar Dados Iniciais

```bash
# Conectar ao shell do Heroku
heroku run python backend/manage.py shell

# No shell Python:
from django.contrib.auth.models import User, Group
from stores.models import Store

# Criar usuário super admin
superadmin = User.objects.create_superuser(
    username='superadmin',
    email='admin@seudominio.com',
    password='senha-super-segura'
)

# Criar usuário de suporte
suporte = User.objects.create_user(
    username='suporte',
    email='suporte@seudominio.com',
    password='senha-suporte',
    is_staff=True
)
grupo_suporte = Group.objects.create(name='suporte')
suporte.groups.add(grupo_suporte)

# Criar loja exemplo
Store.objects.create(
    tenant_slug='loja-tech',
    name='Loja Tech',
    slug='loja-tech',
    description='Produtos de tecnologia',
    owner=superadmin,
    access_type='loja'
)
```

---

## 🎨 Deploy no Render

### Passo 1: Criar Conta

1. Acesse https://render.com
2. Faça login com GitHub

### Passo 2: Criar PostgreSQL

1. Dashboard → New → PostgreSQL
2. Nome: `multistore-db`
3. Plano: Free
4. Criar

### Passo 3: Criar Web Service

1. Dashboard → New → Web Service
2. Conectar repositório GitHub
3. Configurações:
   - **Name**: `multistore-backend`
   - **Environment**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd backend && gunicorn config.wsgi:application
     ```

### Passo 4: Variáveis de Ambiente

No Render, adicione:

```
SECRET_KEY=sua-chave-secreta
DATABASE_URL=postgresql://... (copie do PostgreSQL criado)
ALLOWED_HOSTS=multistore-backend.onrender.com
DJANGO_SETTINGS_MODULE=config.settings_single_db
DEBUG=False
CORS_ORIGINS=https://seu-frontend.vercel.app
```

### Passo 5: Deploy

1. Clique em "Create Web Service"
2. Aguarde o build
3. Acesse o shell:
   ```bash
   python backend/manage.py migrate
   python backend/manage.py createsuperuser
   ```

---

## 🌐 Deploy Frontend (Vercel)

### Passo 1: Preparar Frontend

```bash
cd frontend

# Criar .env.production
echo "NEXT_PUBLIC_API_URL=https://seu-backend.herokuapp.com" > .env.production
```

### Passo 2: Deploy

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel

# Produção
vercel --prod
```

Ou conecte o repositório no dashboard da Vercel.

---

## 🔒 Segurança em Produção

### Checklist:

✅ **SECRET_KEY** diferente do desenvolvimento  
✅ **DEBUG=False** em produção  
✅ **ALLOWED_HOSTS** configurado corretamente  
✅ **HTTPS** habilitado (automático no Heroku/Render)  
✅ **CORS** configurado apenas para domínios confiáveis  
✅ **Senhas fortes** para todos os usuários  
✅ **Backups** configurados  

---

## 📊 Monitoramento

### Heroku:

```bash
# Ver logs em tempo real
heroku logs --tail

# Ver métricas
heroku ps

# Ver banco de dados
heroku pg:info
```

### Render:

- Dashboard → Logs
- Dashboard → Metrics
- Dashboard → Shell

---

## 🔄 Migrations em Produção

```bash
# Heroku
heroku run python backend/manage.py makemigrations
heroku run python backend/manage.py migrate

# Render
# Via Shell no dashboard ou:
render run python backend/manage.py migrate
```

---

## 💰 Custos Estimados

### Heroku:

| Recurso | Plano | Custo |
|---------|-------|-------|
| Dyno | Eco | $5/mês |
| PostgreSQL | Mini | $5/mês |
| **Total** | | **$10/mês** |

### Render:

| Recurso | Plano | Custo |
|---------|-------|-------|
| Web Service | Starter | $7/mês |
| PostgreSQL | Starter | $7/mês |
| **Total** | | **$14/mês** |

### Vercel (Frontend):

| Recurso | Plano | Custo |
|---------|-------|-------|
| Hosting | Hobby | **Grátis** |

---

## 🐛 Troubleshooting

### Erro: "Application Error"
```bash
heroku logs --tail
# Verifique SECRET_KEY e DATABASE_URL
```

### Erro: "Database connection failed"
```bash
heroku pg:info
# Verifique se PostgreSQL está ativo
```

### Erro: "Static files not found"
```bash
heroku run python backend/manage.py collectstatic --noinput
```

---

## 📚 Recursos

- [Heroku Python Guide](https://devcenter.heroku.com/articles/getting-started-with-python)
- [Render Deploy Guide](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

---

## ✅ Checklist de Deploy

- [ ] Criar conta no Heroku/Render
- [ ] Configurar PostgreSQL
- [ ] Configurar variáveis de ambiente
- [ ] Fazer deploy do backend
- [ ] Rodar migrations
- [ ] Criar superusuário
- [ ] Testar API
- [ ] Deploy do frontend
- [ ] Configurar domínio customizado (opcional)
- [ ] Configurar backups
- [ ] Monitorar logs

---

**Sistema otimizado para produção com SINGLE DATABASE!** 🚀
