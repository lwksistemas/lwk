# LWK Sistemas - Sistema Multi-Tenant SaaS

Sistema multi-tenant completo para gestão de diferentes tipos de negócios (clínicas, CRM, e-commerce, etc).

## 🚀 Stack Tecnológica

### Backend
- **Django 4.2** - Framework web Python
- **Django REST Framework** - API REST
- **PostgreSQL** - Banco de dados (Heroku Postgres)
- **Redis** - Cache e sessões
- **Heroku** - Hospedagem backend

### Frontend
- **Next.js 14** - Framework React
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **Zustand** - Gerenciamento de estado
- **Vercel** - Hospedagem frontend

## 📦 Tipos de App Disponíveis

1. **Clínica de Estética** - Sistema para clínicas de estética com agendamentos e prontuários
2. **CRM Vendas** - Gestão de vendas, leads e pipeline comercial
3. **Clínica da Beleza** - Sistema para clínicas de beleza com profissionais e serviços

## 🔧 Configuração Local

### Backend

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env

# Executar migrations
python backend/manage.py migrate

# Criar superusuário
python backend/manage.py createsuperuser

# Iniciar servidor
python backend/manage.py runserver
```

### Frontend

```bash
# Instalar dependências
cd frontend
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local

# Iniciar servidor de desenvolvimento
npm run dev
```

## 🌐 URLs

- **Frontend**: https://lwksistemas.com.br/
- **Backend API**: https://lwksistemas-38ad47519238.herokuapp.com/api/
- **Documentação API**: https://lwksistemas-38ad47519238.herokuapp.com/api/docs/

## 🔐 Credenciais de Acesso (Desenvolvimento)

- **Superusuário**: `admin`
- **CPF**: `00000000000`
- **Senha**: (definida no setup)

## 📚 Documentação

- [Migração Heroku Postgres](MIGRACAO_HEROKU_POSTGRES_v917.md) - Migração do RDS AWS para Heroku Postgres
- [Tipos de App](TIPOS_APP_CRIADOS_v922.md) - Tipos de app disponíveis no sistema

## 🛠️ Comandos Úteis

### Backend

```bash
# Criar tipos de app iniciais
heroku run python backend/manage.py criar_tipos_app_iniciais --app lwksistemas

# Criar UsuarioSistema para admin
heroku run python backend/manage.py criar_usuario_sistema_admin --app lwksistemas

# Migrations
heroku run python backend/manage.py migrate --app lwksistemas

# Logs
heroku logs --tail --app lwksistemas
```

### Frontend

```bash
# Build de produção
npm run build

# Deploy Vercel
vercel --prod
```

## 📊 Estrutura do Projeto

```
lwksistemas/
├── backend/              # Django backend
│   ├── config/          # Configurações Django
│   ├── superadmin/      # App de super admin
│   ├── stores/          # App de lojas
│   ├── products/        # App de produtos
│   ├── crm_vendas/      # App CRM Vendas
│   ├── clinica_estetica/# App Clínica Estética
│   ├── clinica_beleza/  # App Clínica Beleza
│   └── ...
├── frontend/            # Next.js frontend
│   ├── app/            # App Router (Next.js 14)
│   ├── components/     # Componentes React
│   ├── store/          # Zustand stores
│   └── ...
├── requirements.txt    # Dependências Python
└── README.md          # Este arquivo
```

## 🔄 Deploy

### Backend (Heroku)

```bash
git push heroku master
```

### Frontend (Vercel)

```bash
vercel --prod
```

## 📝 Licença

Propriedade de LWK Sistemas. Todos os direitos reservados.

## 📧 Contato

- Email: lwksistemas@gmail.com
- Site: https://lwksistemas.com.br/
