# ⚡ DEPLOY RÁPIDO - v258

> Deploy em 5 minutos usando script automatizado

---

## 🚀 OPÇÃO 1: DEPLOY AUTOMATIZADO (RECOMENDADO)

```bash
# Executar script de deploy
./deploy.sh

# Escolher opção:
# 1) Deploy completo (Backend + Frontend)
# 2) Deploy apenas Backend
# 3) Deploy apenas Frontend
```

**Pronto!** O script faz tudo automaticamente.

---

## 📝 OPÇÃO 2: DEPLOY MANUAL RÁPIDO

### Backend (Heroku)

```bash
# 1. Commit mudanças
git add .
git commit -m "deploy: v258"

# 2. Deploy
git push heroku main

# 3. Migrações
heroku run python backend/manage.py migrate -a lwksistemas

# 4. Testar
curl https://lwksistemas-38ad47519238.herokuapp.com/api/health/
```

### Frontend (Vercel)

```bash
# 1. Deploy
cd frontend
vercel --prod

# 2. Testar
curl -I https://lwksistemas.com.br
```

---

## ✅ CHECKLIST MÍNIMO

### Antes do Deploy
- [ ] Código commitado no Git
- [ ] SECRET_KEY configurada no Heroku
- [ ] ALLOWED_HOSTS configurado
- [ ] CORS_ORIGINS configurado

### Após o Deploy
- [ ] Backend respondendo (health check)
- [ ] Frontend carregando
- [ ] Login funcionando
- [ ] Sem erros nos logs

---

## 🔧 COMANDOS ÚTEIS

```bash
# Ver logs do backend
heroku logs --tail -a lwksistemas

# Ver logs do frontend
vercel logs

# Rollback backend
heroku rollback v123 -a lwksistemas

# Rollback frontend
vercel rollback

# Verificar variáveis de ambiente
heroku config -a lwksistemas
vercel env ls
```

---

## 🚨 PROBLEMAS COMUNS

### Backend não inicia
```bash
# Ver logs
heroku logs --tail -a lwksistemas

# Verificar SECRET_KEY
heroku config:get SECRET_KEY -a lwksistemas
```

### Frontend não conecta
```bash
# Verificar variável
vercel env ls

# Deve ter: NEXT_PUBLIC_API_URL
```

### Erro de CORS
```bash
# Atualizar CORS_ORIGINS
heroku config:set CORS_ORIGINS="https://lwksistemas.com.br" -a lwksistemas
```

---

## 📚 DOCUMENTAÇÃO COMPLETA

Para deploy detalhado, consulte: **[DEPLOY_COMPLETO_v258.md](DEPLOY_COMPLETO_v258.md)**

---

**Tempo estimado:** 5-10 minutos  
**Dificuldade:** Fácil  
**Pré-requisitos:** Heroku CLI, Vercel CLI, Git
