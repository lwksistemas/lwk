# 🚀 Sistema Multi-Loja - Guia Completo de Deploy

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Modo SINGLE vs MULTI](#modo-single-vs-multi)
3. [Deploy Heroku](#deploy-heroku)
4. [Deploy Render](#deploy-render)
5. [Deploy Frontend](#deploy-frontend)
6. [Configuração Pós-Deploy](#configuração-pós-deploy)

---

## 🎯 Visão Geral

Este sistema suporta **2 modos de operação**:

### 🏠 Desenvolvimento Local (MULTI Database)
- 5 bancos SQLite separados
- Isolamento físico total
- Ideal para desenvolvimento e testes

### ☁️ Produção (SINGLE Database)
- 1 banco PostgreSQL
- Isolamento lógico via `tenant_slug`
- **Otimizado para Heroku/Render**

---

## 🔄 Modo SINGLE vs MULTI

| Característica | MULTI (Dev) | SINGLE (Prod) |
|----------------|-------------|---------------|
| Bancos | 5 SQLite | 1 PostgreSQL |
| Heroku/Render | ❌ | ✅ |
| Custo | - | $5-7/mês |
| Queries Cross-Tenant | ❌ | ✅ |
| Backup | 5 separados | 1 unificado |

**Recomendação**: Use SINGLE para produção!

Ver detalhes em: `MODO_SINGLE_VS_MULTI.md`

---

## 🚀 Deploy Heroku

### 1. Pré-requisitos

```bash
# Instalar Heroku CLI
brew install heroku/brew/heroku  # macOS
# ou
curl https://cli-assets.heroku.com/install.sh | sh  # Linux
```

### 2. Criar App

```bash
# Login
heroku login

# Criar app
heroku create seu-app-multistore

# Adicionar PostgreSQL
heroku addons:create heroku-postgresql:mini
```

### 3. Configurar Variáveis

```bash
# Secret Key
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Hosts
heroku config:set ALLOWED_HOSTS=seu-app-multistore.herokuapp.com

# Settings para SINGLE DB
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_single_db

# CORS (se frontend separado)
heroku config:set CORS_ORIGINS=https://seu-frontend.vercel.app
```

### 4. Deploy

```bash
# Adicionar remote
heroku git:remote -a seu-app-multistore

# Deploy
git push heroku main

# Migrations
heroku run python backend/manage.py migrate

# Criar superusuário
heroku run python backend/manage.py createsuperuser
```

### 5. Verificar

```bash
# Ver logs
heroku logs --tail

# Abrir app
heroku open
```

---

## 🎨 Deploy Render

### 1. Criar PostgreSQL

1. Acesse https://render.com
2. New → PostgreSQL
3. Nome: `multistore-db`
4. Plano: Free
5. Criar e copiar `Internal Database URL`

### 2. Criar Web Service

1. New → Web Service
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

### 3. Variáveis de Ambiente

```
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=postgresql://... (do passo 1)
ALLOWED_HOSTS=multistore-backend.onrender.com
DJANGO_SETTINGS_MODULE=config.settings_single_db
DEBUG=False
CORS_ORIGINS=https://seu-frontend.vercel.app
```

### 4. Deploy

1. Clique em "Create Web Service"
2. Aguarde build (~5 min)
3. Acesse Shell e rode:
   ```bash
   python backend/manage.py migrate
   python backend/manage.py createsuperuser
   ```

---

## 🌐 Deploy Frontend (Vercel)

### 1. Preparar

```bash
cd frontend

# Criar .env.production
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://seu-backend.herokuapp.com
EOF
```

### 2. Deploy via CLI

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel

# Produção
vercel --prod
```

### 3. Deploy via Dashboard

1. Acesse https://vercel.com
2. Import Project
3. Conectar repositório
4. Configurar:
   - **Framework**: Next.js
   - **Root Directory**: `frontend`
   - **Environment Variables**:
     ```
     NEXT_PUBLIC_API_URL=https://seu-backend.herokuapp.com
     ```
5. Deploy

---

## ⚙️ Configuração Pós-Deploy

### 1. Criar Dados Iniciais

```bash
# Heroku
heroku run python backend/manage.py shell

# Render
# Via Shell no dashboard
```

```python
from django.contrib.auth.models import User, Group
from stores.models import Store

# Super Admin
superadmin = User.objects.create_superuser(
    username='superadmin',
    email='admin@seudominio.com',
    password='senha-super-segura'
)

# Suporte
suporte = User.objects.create_user(
    username='suporte',
    email='suporte@seudominio.com',
    password='senha-suporte',
    is_staff=True
)
grupo = Group.objects.create(name='suporte')
suporte.groups.add(grupo)

# Loja Exemplo
Store.objects.create(
    tenant_slug='loja-tech',
    name='Loja Tech',
    slug='loja-tech',
    description='Produtos de tecnologia',
    owner=superadmin,
    access_type='loja'
)
```

### 2. Testar Endpoints

```bash
# Health check
curl https://seu-app.herokuapp.com/api/

# Login
curl -X POST https://seu-app.herokuapp.com/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"sua-senha"}'
```

### 3. Configurar Domínio Customizado

#### Heroku:
```bash
heroku domains:add www.seudominio.com
# Configurar DNS conforme instruções
```

#### Render:
1. Dashboard → Settings → Custom Domain
2. Adicionar domínio
3. Configurar DNS

---

## 🔒 Checklist de Segurança

- [ ] `SECRET_KEY` único e forte
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado
- [ ] HTTPS habilitado (automático)
- [ ] CORS apenas para domínios confiáveis
- [ ] Senhas fortes para todos usuários
- [ ] Backups configurados
- [ ] Monitoramento ativo

---

## 💰 Custos Mensais

### Heroku:
- Dyno Eco: $5/mês
- PostgreSQL Mini: $5/mês
- **Total: $10/mês**

### Render:
- Web Service Starter: $7/mês
- PostgreSQL Starter: $7/mês
- **Total: $14/mês**

### Vercel (Frontend):
- Hobby: **Grátis**

---

## 📊 Monitoramento

### Heroku:
```bash
heroku logs --tail
heroku ps
heroku pg:info
```

### Render:
- Dashboard → Logs
- Dashboard → Metrics

---

## 🐛 Troubleshooting

### Erro: "Application Error"
```bash
heroku logs --tail
# Verificar SECRET_KEY e DATABASE_URL
```

### Erro: "Database connection failed"
```bash
heroku pg:info
# Verificar se PostgreSQL está ativo
```

### Erro: "Static files not found"
```bash
heroku run python backend/manage.py collectstatic --noinput
```

---

## 📚 Documentação Adicional

- `DEPLOY_HEROKU_RENDER.md` - Guia detalhado
- `MODO_SINGLE_VS_MULTI.md` - Comparação de modos
- `ARQUITETURA_3_BANCOS.md` - Arquitetura completa

---

## ✅ Checklist Final

- [ ] Backend deployado
- [ ] PostgreSQL configurado
- [ ] Migrations executadas
- [ ] Superusuário criado
- [ ] Frontend deployado
- [ ] Variáveis de ambiente configuradas
- [ ] CORS configurado
- [ ] Domínio customizado (opcional)
- [ ] Backups configurados
- [ ] Monitoramento ativo

---

**Sistema pronto para produção!** 🚀  
**Modo SINGLE otimizado para Heroku/Render** ✨
