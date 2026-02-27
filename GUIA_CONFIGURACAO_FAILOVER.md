# 🚀 Guia Rápido: Configuração do Failover Automático

## Status Atual

✅ **Backend**: Implementado e funcionando (v750-v752)  
✅ **Frontend**: Código implementado (v753)  
⚠️ **Configuração**: Pendente (variáveis de ambiente)

---

## Passo 1: Configurar Servidor Backup no Render

### 1.1. Criar Conta no Render
1. Acesse: https://render.com
2. Faça login com GitHub
3. Autorize acesso ao repositório `lwksistemas`

### 1.2. Criar Web Service
1. Clique em "New +" → "Web Service"
2. Selecione o repositório `lwksistemas`
3. Configure:
   - **Name**: `lwksistemas-backup`
   - **Region**: Oregon (US West) - mesma região do Heroku
   - **Branch**: `master`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

### 1.3. Configurar Variáveis de Ambiente

Copie TODAS as variáveis de ambiente do Heroku:

```bash
# Listar variáveis do Heroku
heroku config -a lwksistemas

# Adicionar no Render (via Dashboard):
# Settings → Environment → Add Environment Variable
```

**Variáveis Obrigatórias**:
- `DATABASE_URL`: URL do PostgreSQL do Heroku
- `SECRET_KEY`: Mesma chave do Heroku
- `DEBUG`: False
- `ALLOWED_HOSTS`: lwksistemas.onrender.com,lwksistemas-38ad47519238.herokuapp.com
- `CORS_ALLOWED_ORIGINS`: https://lwksistemas.com.br
- `REDIS_URL`: URL do Redis do Heroku
- `ASAAS_API_KEY`: Chave da API Asaas
- `MERCADOPAGO_ACCESS_TOKEN`: Token do Mercado Pago
- Todas as outras variáveis do Heroku

### 1.4. Deploy
1. Clique em "Create Web Service"
2. Aguarde o deploy (5-10 minutos)
3. Anote a URL: `https://lwksistemas.onrender.com`

### 1.5. Testar
```bash
# Testar health check
curl https://lwksistemas.onrender.com/api/superadmin/health/

# Deve retornar:
# {"status": "healthy", "database": "connected", "lojas_count": 4}
```

---

## Passo 2: Configurar Variáveis no Vercel

### 2.1. Via Dashboard (Recomendado)

1. Acesse: https://vercel.com/lwks-projects-48afd555/frontend/settings/environment-variables
2. Adicione as variáveis:

| Key | Value | Environment |
|-----|-------|-------------|
| `NEXT_PUBLIC_API_BACKUP_URL` | `https://lwksistemas.onrender.com` | Production |
| `NEXT_PUBLIC_API_TIMEOUT` | `20000` | Production |

3. Clique em "Save"

### 2.2. Via CLI (Alternativa)

```bash
cd frontend

# Adicionar variável de backup
vercel env add NEXT_PUBLIC_API_BACKUP_URL production
# Quando solicitado, digite: https://lwksistemas.onrender.com

# Adicionar timeout
vercel env add NEXT_PUBLIC_API_TIMEOUT production
# Quando solicitado, digite: 20000

# Fazer redeploy para aplicar as variáveis
vercel --prod
```

---

## Passo 3: Testar o Failover

### 3.1. Verificar Status Inicial

```bash
# Abrir console do navegador em https://lwksistemas.com.br
# Colar e executar:
```

```javascript
// Importar funções (se disponível no console)
// Ou verificar logs de requisições

// Verificar que está usando Heroku
console.log('API atual:', process.env.NEXT_PUBLIC_API_URL);
```

### 3.2. Simular Falha do Heroku

```bash
# Desligar dyno do Heroku temporariamente
heroku ps:scale web=0 -a lwksistemas

# Aguardar 30 segundos para garantir que está offline
```

### 3.3. Testar Failover

1. Acesse: https://lwksistemas.com.br/superadmin/dashboard
2. Faça login
3. Navegue pelo sistema
4. Observe o console do navegador:
   - Deve mostrar: "⚠️ API primária falhou, tentando backup..."
   - Deve mostrar: "🔄 Repetindo requisição no servidor backup..."
   - Sistema deve continuar funcionando normalmente

### 3.4. Reativar Heroku

```bash
# Reativar dyno do Heroku
heroku ps:scale web=1 -a lwksistemas

# Aguardar 5 minutos
# Sistema deve voltar automaticamente para Heroku
# Console deve mostrar: "✅ Voltando para API primária após 5 minutos de sucesso"
```

---

## Passo 4: Monitoramento

### 4.1. Verificar Logs do Heroku

```bash
# Ver logs em tempo real
heroku logs --tail -a lwksistemas

# Filtrar apenas health checks
heroku logs --tail -a lwksistemas | grep health
```

### 4.2. Verificar Logs do Render

1. Acesse: https://dashboard.render.com
2. Clique no serviço `lwksistemas-backup`
3. Vá em "Logs"
4. Monitore requisições

### 4.3. Configurar Alertas (Opcional)

**UptimeRobot** (Gratuito):
1. Acesse: https://uptimerobot.com
2. Adicione 2 monitores:
   - Heroku: `https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/health/`
   - Render: `https://lwksistemas.onrender.com/api/superadmin/health/`
3. Configure alertas por email

---

## Troubleshooting

### Problema: Render não conecta ao banco

**Solução**: Verificar se o IP do Render está na whitelist do PostgreSQL do Heroku

```bash
# Adicionar IP do Render ao PostgreSQL
heroku pg:credentials:attach -a lwksistemas
```

### Problema: CORS error no Render

**Solução**: Adicionar URL do Render no `CORS_ALLOWED_ORIGINS`

```bash
# No Heroku
heroku config:set CORS_ALLOWED_ORIGINS="https://lwksistemas.com.br,https://lwksistemas.onrender.com" -a lwksistemas

# No Render (via Dashboard)
# Adicionar mesma variável
```

### Problema: Failover não ativa

**Solução**: Verificar se as variáveis de ambiente estão configuradas no Vercel

```bash
# Listar variáveis do Vercel
vercel env ls

# Deve mostrar:
# NEXT_PUBLIC_API_BACKUP_URL
# NEXT_PUBLIC_API_TIMEOUT
```

### Problema: Render muito lento

**Solução**: Render free tier "dorme" após 15 minutos de inatividade. Considere:
1. Upgrade para plano pago ($7/mês)
2. Ou usar serviço de "keep alive" (ping a cada 10 minutos)

---

## Checklist de Configuração

- [ ] Conta criada no Render
- [ ] Web Service criado no Render
- [ ] Variáveis de ambiente configuradas no Render
- [ ] Deploy do Render concluído com sucesso
- [ ] Health check do Render funcionando
- [ ] Variável `NEXT_PUBLIC_API_BACKUP_URL` adicionada no Vercel
- [ ] Variável `NEXT_PUBLIC_API_TIMEOUT` adicionada no Vercel
- [ ] Redeploy do frontend no Vercel
- [ ] Teste de failover realizado
- [ ] Recuperação automática testada
- [ ] Monitoramento configurado (opcional)

---

## Comandos Úteis

```bash
# Verificar health do Heroku
curl https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/health/

# Verificar health do Render
curl https://lwksistemas.onrender.com/api/superadmin/health/

# Ver logs do Heroku
heroku logs --tail -a lwksistemas

# Desligar Heroku (teste)
heroku ps:scale web=0 -a lwksistemas

# Ligar Heroku
heroku ps:scale web=1 -a lwksistemas

# Ver variáveis do Vercel
vercel env ls

# Redeploy do Vercel
cd frontend && vercel --prod
```

---

## Suporte

Se encontrar problemas:
1. Verifique os logs do Heroku e Render
2. Verifique o console do navegador
3. Confirme que todas as variáveis de ambiente estão configuradas
4. Teste o health check de ambos os servidores

---

**Data**: 27/02/2026  
**Versão**: v750-v753  
**Status**: ✅ Pronto para configuração
