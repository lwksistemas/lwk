# ✅ Checklist: Configurar Render

## 📋 Passo a Passo Rápido

### ☐ 1. Login no Render
- [ ] Acesse: https://dashboard.render.com/register
- [ ] Clique em "Sign in with GitHub"
- [ ] Autorize o Render

### ☐ 2. Criar Web Service
- [ ] Acesse: https://dashboard.render.com/select-repo?type=web
- [ ] Encontre o repositório "lwksistemas"
- [ ] Clique em "Connect"

### ☐ 3. Configuração Básica

Preencha exatamente assim:

- [ ] **Name**: `lwksistemas-backup`
- [ ] **Region**: `Oregon (US West)`
- [ ] **Branch**: `master`
- [ ] **Root Directory**: `backend`
- [ ] **Runtime**: `Python 3`
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- [ ] **Instance Type**: `Free`

### ☐ 4. Adicionar Variáveis de Ambiente

Role até "Environment Variables" e adicione TODAS as 17 variáveis do arquivo **`VARIAVEIS_RENDER.txt`**

**Como adicionar cada variável:**
1. Clique em "Add Environment Variable"
2. Cole o **Key** (nome)
3. Cole o **Value** (valor)
4. Clique em "Add"
5. Repita para todas

**Variáveis obrigatórias** (total: 17):
- [ ] ALLOWED_HOSTS
- [ ] ASAAS_API_KEY
- [ ] ASAAS_INTEGRATION_ENABLED
- [ ] ASAAS_SANDBOX
- [ ] CONN_MAX_AGE
- [ ] CORS_ORIGINS
- [ ] DATABASE_URL
- [ ] DEBUG
- [ ] DJANGO_SETTINGS_MODULE
- [ ] EMAIL_HOST
- [ ] EMAIL_HOST_PASSWORD
- [ ] EMAIL_HOST_USER
- [ ] EMAIL_PORT
- [ ] EMAIL_USE_TLS
- [ ] REDIS_URL
- [ ] SECRET_KEY
- [ ] SECURITY_NOTIFICATION_EMAILS
- [ ] SITE_URL
- [ ] USE_REDIS

### ☐ 5. Deploy
- [ ] Role até o final da página
- [ ] Clique em "Create Web Service"
- [ ] Aguarde 5-10 minutos (acompanhe os logs)

### ☐ 6. Verificar Deploy
- [ ] Aguarde até ver "Your service is live 🎉"
- [ ] Anote a URL: `https://lwksistemas-backup.onrender.com`

### ☐ 7. Testar Health Check

Execute no terminal:
```bash
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
```

Resposta esperada:
```json
{
  "status": "healthy",
  "database": "connected",
  "lojas_count": 4
}
```

### ☐ 8. Configurar Vercel

Acesse: https://vercel.com/lwks-projects-48afd555/frontend/settings/environment-variables

Adicione 2 variáveis:

**Variável 1:**
- [ ] Key: `NEXT_PUBLIC_API_BACKUP_URL`
- [ ] Value: `https://lwksistemas-backup.onrender.com`
- [ ] Environment: Production

**Variável 2:**
- [ ] Key: `NEXT_PUBLIC_API_TIMEOUT`
- [ ] Value: `20000`
- [ ] Environment: Production

### ☐ 9. Redeploy Frontend

Execute no terminal:
```bash
cd frontend
vercel --prod
```

Ou via Dashboard:
- [ ] Vá em "Deployments"
- [ ] Clique nos 3 pontinhos do último deploy
- [ ] Clique em "Redeploy"

### ☐ 10. Testar Failover

**Desligar Heroku:**
```bash
heroku ps:scale web=0 -a lwksistemas
```

**Testar sistema:**
- [ ] Acesse: https://lwksistemas.com.br/superadmin/dashboard
- [ ] Faça login
- [ ] Navegue pelo sistema
- [ ] Abra o Console (F12) e veja mensagens de failover
- [ ] Sistema deve continuar funcionando!

**Reativar Heroku:**
```bash
heroku ps:scale web=1 -a lwksistemas
```

**Verificar recuperação:**
- [ ] Aguarde 5 minutos
- [ ] Sistema deve voltar para Heroku automaticamente
- [ ] Console mostra: "✅ Voltando para API primária"

---

## 🎉 Conclusão

Quando todos os itens estiverem marcados, você terá:

✅ Servidor backup no Render (gratuito)
✅ Failover automático configurado
✅ Sistema com alta disponibilidade
✅ Custo zero adicional

---

## 📚 Arquivos de Ajuda

- **VARIAVEIS_RENDER.txt**: Todas as variáveis para copiar/colar
- **PASSO_A_PASSO_RENDER.md**: Guia detalhado com explicações
- **IMPLEMENTACAO_FAILOVER_v750.md**: Documentação técnica completa

---

## 🆘 Precisa de Ajuda?

Se tiver dúvidas em algum passo:
1. Consulte o arquivo `PASSO_A_PASSO_RENDER.md`
2. Verifique os logs do Render
3. Teste o health check
4. Verifique se todas as variáveis foram adicionadas

---

**Tempo estimado: 20-30 minutos**

Boa sorte! 🚀
