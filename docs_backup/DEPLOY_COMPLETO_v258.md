# 🚀 GUIA COMPLETO DE DEPLOY - v258

**Data:** 30/01/2026  
**Sistema:** LWK Sistemas Multi-Tenant SaaS  
**Backend:** Heroku (Django + PostgreSQL)  
**Frontend:** Vercel (Next.js)

---

## 📋 PRÉ-REQUISITOS

### Contas Necessárias
- ✅ Heroku Account (backend)
- ✅ Vercel Account (frontend)
- ✅ GitHub Account (código)
- ✅ Domínio configurado (lwksistemas.com.br)

### Ferramentas Instaladas
```bash
# Verificar instalações
heroku --version
vercel --version
git --version
python --version
node --version
```

---

## 🔧 PARTE 1: PREPARAÇÃO DO CÓDIGO

### 1.1 Aplicar Otimizações de Segurança

```bash
# Importar settings de segurança
echo "" >> backend/config/settings_production.py
echo "# Importar otimizações de segurança v258" >> backend/config/settings_production.py
echo "try:" >> backend/config/settings_production.py
echo "    from .settings_security import *" >> backend/config/settings_production.py
echo "except ImportError:" >> backend/config/settings_production.py
echo "    pass" >> backend/config/settings_production.py
```

### 1.2 Gerar SECRET_KEY Segura

```bash
# Gerar nova SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copiar o resultado e guardar para usar no Heroku
```

### 1.3 Atualizar Requirements

```bash
# Verificar se todas as dependências estão no requirements.txt
cd backend
pip freeze > requirements.txt

# Adicionar dependências de produção se necessário
echo "gunicorn==21.2.0" >> requirements.txt
echo "dj-database-url==2.1.0" >> requirements.txt
echo "psycopg2-binary==2.9.9" >> requirements.txt
echo "whitenoise==6.6.0" >> requirements.txt
echo "django-redis==5.4.0" >> requirements.txt
```

### 1.4 Commit das Mudanças

```bash
# Voltar para raiz
cd ..

# Adicionar arquivos
git add .

# Commit
git commit -m "feat: aplicar otimizações de segurança e performance v258"

# Push para GitHub
git push origin main
```

---

## 🐳 PARTE 2: DEPLOY DO BACKEND (HEROKU)

### 2.1 Login no Heroku

```bash
heroku login
```

### 2.2 Verificar App Existente

```bash
# Listar apps
heroku apps

# Verificar app atual
heroku apps:info lwksistemas

# Se não existir, criar:
# heroku create lwksistemas
```

### 2.3 Configurar Variáveis de Ambiente

```bash
# SECRET_KEY (usar a gerada no passo 1.2)
heroku config:set SECRET_KEY="sua-secret-key-aqui" -a lwksistemas

# DEBUG
heroku config:set DEBUG=False -a lwksistemas

# ALLOWED_HOSTS
heroku config:set ALLOWED_HOSTS="lwksistemas-38ad47519238.herokuapp.com,lwksistemas.com.br,www.lwksistemas.com.br" -a lwksistemas

# CORS_ORIGINS
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br,https://frontend-r3q0a1lw4-lwks-projects-48afd555.vercel.app" -a lwksistemas

# EMAIL
heroku config:set EMAIL_HOST_USER="lwksistemas@gmail.com" -a lwksistemas
heroku config:set EMAIL_HOST_PASSWORD="cabbshvjjbcjagzh" -a lwksistemas

# ASAAS (se usar)
heroku config:set ASAAS_API_KEY="sua-chave-asaas" -a lwksistemas
heroku config:set ASAAS_SANDBOX="True" -a lwksistemas

# DJANGO_SETTINGS_MODULE
heroku config:set DJANGO_SETTINGS_MODULE="config.settings_production" -a lwksistemas

# Segurança (novas configurações v258)
heroku config:set SECURE_SSL_REDIRECT="True" -a lwksistemas
heroku config:set SESSION_COOKIE_SECURE="True" -a lwksistemas
heroku config:set CSRF_COOKIE_SECURE="True" -a lwksistemas
```

### 2.4 Adicionar PostgreSQL

```bash
# Verificar se já tem PostgreSQL
heroku addons -a lwksistemas

# Se não tiver, adicionar (plano gratuito)
heroku addons:create heroku-postgresql:essential-0 -a lwksistemas

# Verificar DATABASE_URL
heroku config:get DATABASE_URL -a lwksistemas
```

### 2.5 Adicionar Redis (Opcional - Recomendado)

```bash
# Adicionar Redis para cache
heroku addons:create heroku-redis:mini -a lwksistemas

# Verificar REDIS_URL
heroku config:get REDIS_URL -a lwksistemas
```

### 2.6 Deploy do Backend

```bash
# Fazer deploy
git push heroku main

# Ou se estiver em outra branch
git push heroku sua-branch:main
```

### 2.7 Executar Migrações

```bash
# Executar migrações
heroku run python backend/manage.py migrate -a lwksistemas

# Coletar arquivos estáticos
heroku run python backend/manage.py collectstatic --noinput -a lwksistemas

# Criar superusuário (se necessário)
heroku run python backend/manage.py createsuperuser -a lwksistemas
```

### 2.8 Verificar Logs

```bash
# Ver logs em tempo real
heroku logs --tail -a lwksistemas

# Ver logs de erro
heroku logs --tail -a lwksistemas | grep ERROR
```

### 2.9 Testar Backend

```bash
# Testar health check
curl https://lwksistemas-38ad47519238.herokuapp.com/api/health/

# Testar login
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua-senha"}'
```

---

## ⚡ PARTE 3: DEPLOY DO FRONTEND (VERCEL)

### 3.1 Login no Vercel

```bash
vercel login
```

### 3.2 Configurar Variáveis de Ambiente

```bash
# Via CLI
vercel env add NEXT_PUBLIC_API_URL production
# Valor: https://lwksistemas-38ad47519238.herokuapp.com

# Ou via Dashboard Vercel:
# 1. Acessar https://vercel.com/dashboard
# 2. Selecionar projeto
# 3. Settings > Environment Variables
# 4. Adicionar: NEXT_PUBLIC_API_URL = https://lwksistemas-38ad47519238.herokuapp.com
```

### 3.3 Verificar Configurações do Projeto

```bash
# Verificar vercel.json
cat frontend/vercel.json

# Verificar .env.production
cat frontend/.env.production
```

### 3.4 Deploy do Frontend

```bash
# Entrar na pasta frontend
cd frontend

# Deploy para produção
vercel --prod

# Ou via Git (automático)
# Vercel detecta push no GitHub e faz deploy automático
```

### 3.5 Configurar Domínio

```bash
# Adicionar domínio customizado
vercel domains add lwksistemas.com.br

# Adicionar www
vercel domains add www.lwksistemas.com.br

# Verificar domínios
vercel domains ls
```

### 3.6 Testar Frontend

```bash
# Abrir no navegador
open https://lwksistemas.com.br

# Ou testar com curl
curl -I https://lwksistemas.com.br
```

---

## 🔒 PARTE 4: CONFIGURAÇÕES DE SEGURANÇA

### 4.1 Verificar Headers de Segurança

```bash
# Testar headers do backend
curl -I https://lwksistemas-38ad47519238.herokuapp.com/api/health/

# Deve retornar:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
```

### 4.2 Verificar HTTPS

```bash
# Backend
curl -I http://lwksistemas-38ad47519238.herokuapp.com/api/health/
# Deve redirecionar para HTTPS

# Frontend
curl -I http://lwksistemas.com.br
# Deve redirecionar para HTTPS
```

### 4.3 Testar Rate Limiting

```bash
# Tentar login 6 vezes seguidas
for i in {1..6}; do
  curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"wrong"}'
  echo "\nTentativa $i"
  sleep 1
done

# A 6ª tentativa deve retornar erro 429 (Too Many Requests)
```

### 4.4 Verificar CORS

```bash
# Testar CORS
curl -H "Origin: https://lwksistemas.com.br" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS \
  https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/

# Deve retornar headers CORS corretos
```

---

## 📊 PARTE 5: MONITORAMENTO E VALIDAÇÃO

### 5.1 Verificar Performance

```bash
# Testar tempo de resposta
time curl https://lwksistemas-38ad47519238.herokuapp.com/api/health/

# Deve ser < 500ms
```

### 5.2 Verificar Logs

```bash
# Backend (Heroku)
heroku logs --tail -a lwksistemas

# Frontend (Vercel)
vercel logs
```

### 5.3 Verificar Banco de Dados

```bash
# Conectar ao PostgreSQL
heroku pg:psql -a lwksistemas

# Verificar tabelas
\dt

# Verificar número de lojas
SELECT COUNT(*) FROM superadmin_loja;

# Sair
\q
```

### 5.4 Verificar Cache

```bash
# Se usando Redis
heroku redis:cli -a lwksistemas

# Verificar keys
KEYS *

# Verificar info
INFO

# Sair
exit
```

---

## 🧪 PARTE 6: TESTES DE INTEGRAÇÃO

### 6.1 Testar Fluxo Completo

```bash
# 1. Acessar frontend
open https://lwksistemas.com.br

# 2. Fazer login como superadmin
# 3. Criar uma loja
# 4. Fazer login na loja
# 5. Criar um cliente
# 6. Criar um agendamento
# 7. Verificar dashboard
```

### 6.2 Testar Isolamento de Tenant

```bash
# 1. Login em loja 1
# 2. Criar dados
# 3. Logout
# 4. Login em loja 2
# 5. Verificar que não vê dados da loja 1
```

### 6.3 Testar Performance

```bash
# Usar ferramenta de benchmark
ab -n 100 -c 10 https://lwksistemas-38ad47519238.herokuapp.com/api/health/

# Ou usar Apache Bench
# -n 100: 100 requests
# -c 10: 10 concurrent
```

---

## 🔧 PARTE 7: TROUBLESHOOTING

### 7.1 Backend não inicia

```bash
# Ver logs
heroku logs --tail -a lwksistemas

# Verificar variáveis de ambiente
heroku config -a lwksistemas

# Verificar Procfile
cat backend/Procfile

# Deve conter:
# web: gunicorn config.wsgi --chdir backend
```

### 7.2 Erro de Migração

```bash
# Resetar migrações (CUIDADO: apaga dados)
heroku pg:reset -a lwksistemas
heroku run python backend/manage.py migrate -a lwksistemas
```

### 7.3 Erro de CORS

```bash
# Verificar CORS_ORIGINS
heroku config:get CORS_ORIGINS -a lwksistemas

# Atualizar se necessário
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br,https://www.lwksistemas.com.br" -a lwksistemas
```

### 7.4 Frontend não conecta ao Backend

```bash
# Verificar variável de ambiente no Vercel
vercel env ls

# Verificar .env.production
cat frontend/.env.production

# Deve conter:
# NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
```

### 7.5 Erro 500 no Backend

```bash
# Ver logs detalhados
heroku logs --tail -a lwksistemas | grep ERROR

# Verificar SECRET_KEY
heroku config:get SECRET_KEY -a lwksistemas

# Verificar DEBUG
heroku config:get DEBUG -a lwksistemas
# Deve ser False
```

---

## 📋 CHECKLIST FINAL

### Backend (Heroku)
- [ ] App criado no Heroku
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado (opcional)
- [ ] Variáveis de ambiente configuradas
- [ ] SECRET_KEY segura configurada
- [ ] ALLOWED_HOSTS configurado
- [ ] CORS_ORIGINS configurado
- [ ] Deploy realizado
- [ ] Migrações executadas
- [ ] Arquivos estáticos coletados
- [ ] Logs sem erros
- [ ] Health check funcionando
- [ ] HTTPS forçado
- [ ] Headers de segurança configurados

### Frontend (Vercel)
- [ ] Projeto conectado ao GitHub
- [ ] Variáveis de ambiente configuradas
- [ ] NEXT_PUBLIC_API_URL configurado
- [ ] Deploy realizado
- [ ] Domínio customizado configurado
- [ ] www redirecionando para domínio principal
- [ ] HTTPS funcionando
- [ ] Headers de segurança configurados
- [ ] Cache configurado

### Segurança
- [ ] SECRET_KEY única e segura
- [ ] DEBUG=False em produção
- [ ] HTTPS forçado
- [ ] CORS restritivo
- [ ] Rate limiting funcionando
- [ ] Headers de segurança configurados
- [ ] Cookies seguros (Secure, HttpOnly)

### Performance
- [ ] Cache configurado (Redis ou LocMem)
- [ ] Arquivos estáticos comprimidos
- [ ] GZip habilitado
- [ ] Connection pooling configurado
- [ ] Tempo de resposta < 500ms

### Funcionalidade
- [ ] Login funcionando
- [ ] Criação de loja funcionando
- [ ] Isolamento de tenant funcionando
- [ ] Dashboard carregando
- [ ] CRUD de dados funcionando
- [ ] Email funcionando

---

## 🚀 COMANDOS RÁPIDOS

### Deploy Rápido (após primeira configuração)

```bash
# Backend
git add .
git commit -m "update: deploy v258"
git push heroku main
heroku run python backend/manage.py migrate -a lwksistemas

# Frontend
cd frontend
vercel --prod
cd ..
```

### Rollback (se algo der errado)

```bash
# Backend
heroku releases -a lwksistemas
heroku rollback v123 -a lwksistemas  # Substituir v123 pela versão anterior

# Frontend
vercel rollback
```

### Ver Status

```bash
# Backend
heroku ps -a lwksistemas
heroku logs --tail -a lwksistemas

# Frontend
vercel ls
vercel logs
```

---

## 📞 SUPORTE

### URLs Importantes

- **Backend:** https://lwksistemas-38ad47519238.herokuapp.com
- **Frontend:** https://lwksistemas.com.br
- **Heroku Dashboard:** https://dashboard.heroku.com/apps/lwksistemas
- **Vercel Dashboard:** https://vercel.com/dashboard

### Documentação

- Heroku: https://devcenter.heroku.com/
- Vercel: https://vercel.com/docs
- Django: https://docs.djangoproject.com/
- Next.js: https://nextjs.org/docs

---

**Criado em:** 30/01/2026  
**Versão:** v258  
**Status:** ✅ Pronto para Deploy
