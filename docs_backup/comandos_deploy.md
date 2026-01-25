# 🚀 Comandos de Deploy

## Configurar Ambiente
```bash
# Executar sempre antes de usar os CLIs
source ./setup_cli_env.sh
```

## Vercel (Frontend)

### Deploy do Frontend
```bash
cd frontend
vercel --prod
```

### Deploy de Preview
```bash
cd frontend
vercel
```

### Ver deployments
```bash
vercel list
```

### Ver logs
```bash
vercel logs [deployment-url]
```

## Heroku (Backend)

### Criar app no Heroku
```bash
heroku create lwk-sistemas-backend
```

### Adicionar PostgreSQL
```bash
heroku addons:create heroku-postgresql:mini -a lwk-sistemas-backend
```

### Configurar variáveis de ambiente
```bash
heroku config:set SECRET_KEY="sua-secret-key" -a lwk-sistemas-backend
heroku config:set DEBUG=False -a lwk-sistemas-backend
heroku config:set DJANGO_SETTINGS_MODULE=config.settings_production -a lwk-sistemas-backend
```

### Deploy do Backend
```bash
cd backend
git add .
git commit -m "Deploy to Heroku"
heroku git:remote -a lwk-sistemas-backend
git push heroku main
```

### Executar migrations
```bash
heroku run python manage.py migrate -a lwk-sistemas-backend
```

### Criar superuser
```bash
heroku run python manage.py createsuperuser -a lwk-sistemas-backend
```

### Ver logs
```bash
heroku logs --tail -a lwk-sistemas-backend
```

## Status dos CLIs

✅ **Vercel CLI**: Instalado e logado
- Conta: lwks-projects-48afd555
- URL: https://vercel.com/lwks-projects-48afd555

✅ **Heroku CLI**: Instalado e logado  
- Email: lwksistemas@gmail.com
- Versão: 7.69.1

## Comandos Úteis

### Verificar status de login
```bash
vercel whoami
heroku auth:whoami
```

### Logout (se necessário)
```bash
vercel logout
heroku auth:logout
```

### Login novamente
```bash
vercel login
heroku login
```