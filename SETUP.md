# Guia de Setup Detalhado

## Pré-requisitos

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- Git

## 1. Configuração do Backend

### 1.1 Criar Banco de Dados

```bash
# PostgreSQL
psql -U postgres
CREATE DATABASE multistore_db;
CREATE USER multistore_user WITH PASSWORD 'sua_senha';
ALTER ROLE multistore_user SET client_encoding TO 'utf8';
ALTER ROLE multistore_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE multistore_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE multistore_db TO multistore_user;
\q
```

### 1.2 Configurar Ambiente Python

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 1.3 Configurar Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite `.env`:
```env
SECRET_KEY=gere-uma-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://multistore_user:sua_senha@localhost:5432/multistore_db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 1.4 Executar Migrations

```bash
# Migrations do schema compartilhado
python manage.py migrate_schemas --shared

# Migrations dos apps
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser
```

### 1.5 Criar Tenant de Teste (Opcional)

```bash
python manage.py shell
```

```python
from tenants.models import Tenant, Domain

# Criar tenant público
tenant = Tenant(schema_name='public', name='Public')
tenant.save()

domain = Domain()
domain.domain = 'localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()

# Criar tenant de teste
tenant = Tenant(schema_name='loja1', name='Loja 1')
tenant.save()

domain = Domain()
domain.domain = 'loja1.localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()
```

### 1.6 Rodar Servidor

```bash
python manage.py runserver
```

Teste: http://localhost:8000/admin

## 2. Configuração do Frontend

### 2.1 Instalar Dependências

```bash
cd frontend
npm install
```

### 2.2 Configurar Variáveis de Ambiente

```bash
cp .env.local.example .env.local
```

Edite `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2.3 Rodar Servidor de Desenvolvimento

```bash
npm run dev
```

Acesse: http://localhost:3000

## 3. Criar Dados de Teste

### 3.1 Via Django Admin

1. Acesse http://localhost:8000/admin
2. Login com superusuário
3. Crie lojas em "Stores"
4. Crie produtos em "Products"

### 3.2 Via Django Shell

```bash
cd backend
python manage.py shell
```

```python
from django.contrib.auth.models import User
from stores.models import Store
from products.models import Product

# Criar usuário
user = User.objects.create_user('teste', 'teste@email.com', 'senha123')

# Criar loja
store = Store.objects.create(
    name='Minha Loja',
    slug='minha-loja',
    description='Descrição da loja',
    owner=user
)

# Criar produtos
Product.objects.create(
    store=store,
    name='Produto 1',
    slug='produto-1',
    description='Descrição do produto',
    price=99.90,
    stock=10
)

Product.objects.create(
    store=store,
    name='Produto 2',
    slug='produto-2',
    description='Outro produto',
    price=149.90,
    stock=5
)
```

## 4. Testar o Sistema

### 4.1 Login no Frontend

1. Acesse http://localhost:3000
2. Será redirecionado para /login
3. Use as credenciais criadas
4. Após login, verá o dashboard

### 4.2 Testar API Diretamente

```bash
# Obter token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"senha123"}'

# Usar token para acessar API
curl http://localhost:8000/api/stores/ \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 5. Troubleshooting

### Erro de conexão com banco
- Verifique se PostgreSQL está rodando
- Confirme credenciais no .env
- Teste conexão: `psql -U multistore_user -d multistore_db`

### Erro de CORS
- Verifique CORS_ORIGINS no backend/.env
- Confirme que frontend está em http://localhost:3000

### Erro de migrations
```bash
# Resetar migrations (CUIDADO: apaga dados)
python manage.py migrate_schemas --shared
python manage.py migrate --fake-initial
```

### Erro no frontend
```bash
# Limpar cache
rm -rf .next
npm run dev
```

## 6. Deploy em Produção

Ver README.md seção "Deploy" para instruções de Heroku e Render.

## 7. Comandos Úteis

```bash
# Backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py test

# Frontend
npm run build
npm run start
npm run lint
```
