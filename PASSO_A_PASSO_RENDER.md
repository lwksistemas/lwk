# Passo a Passo: Configurar Servidor de Backup no Render

## 🎯 Objetivo

Configurar o servidor de backup no Render com banco de dados separado.

## ⏱️ Tempo Estimado

15-20 minutos

## 📋 Pré-requisitos

- ✅ Conta no Render (https://render.com)
- ✅ Heroku CLI instalado
- ✅ PostgreSQL client instalado (`pg_restore`)

## 🚀 Passo a Passo

### Passo 1: Criar Banco de Dados no Render (5 min)

1. **Acesse:** https://dashboard.render.com/

2. **Clique em:** `New +` (canto superior direito)

3. **Selecione:** `PostgreSQL`

4. **Configure:**
   ```
   Name: lwksistemas-db
   Database: lwksistemas
   User: (gerado automaticamente)
   Region: Oregon
   PostgreSQL Version: 16 (ou mais recente)
   Plan: Starter ($7/mês) ou Free (para testes)
   ```

5. **Clique em:** `Create Database`

6. **Aguarde:** 2-3 minutos até o status ficar "Available"

7. **Copie:** A "Internal Database URL"
   - Exemplo: `postgres://lwksistemas_user:senha@dpg-xxxxx.oregon-postgres.render.com/lwksistemas`

### Passo 2: Copiar Dados do Heroku (5 min)

**Opção A: Usar Script Automatizado (Recomendado)**

```bash
./scripts/setup_render_database.sh
```

Siga as instruções do script.

**Opção B: Manual**

```bash
# 1. Fazer backup do Heroku
heroku pg:backups:capture --app lwksistemas

# 2. Baixar backup
heroku pg:backups:download --app lwksistemas -o /tmp/backup.dump

# 3. Restaurar no Render (cole a URL do Render)
pg_restore --verbose --clean --no-acl --no-owner \
  -d "postgres://user:senha@host/db?sslmode=require" \
  /tmp/backup.dump

# 4. Limpar
rm /tmp/backup.dump
```

### Passo 3: Configurar Variáveis no Render (5 min)

1. **Acesse:** https://dashboard.render.com/

2. **Vá em:** `lwksistemas-backup` (Web Service)

3. **Clique em:** `Environment` (menu lateral)

4. **Adicione as variáveis:**

```bash
# Copiar variáveis do Heroku
./scripts/configurar_render_backup.sh > /tmp/render_env.txt

# Abrir arquivo
cat /tmp/render_env.txt
```

5. **Cole as variáveis no painel do Render:**

**Variáveis Críticas:**
```
SECRET_KEY=<mesmo_do_heroku>
DATABASE_URL=<url_do_banco_render>?sslmode=require
ALLOWED_HOSTS=lwksistemas-backup.onrender.com,.onrender.com
SITE_URL=https://lwksistemas-backup.onrender.com
FRONTEND_URL=https://lwksistemas.com.br
```

**Outras variáveis:**
- EMAIL_HOST, EMAIL_PORT, etc.
- ASAAS_API_KEY, ASAAS_WALLET_ID
- CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, etc.
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
- REDIS_URL (opcional)

6. **Clique em:** `Save Changes`

7. **Aguarde:** Deploy automático (5-10 minutos)

### Passo 4: Testar o Servidor (2 min)

```bash
# Testar health check
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/

# Deve retornar:
# {"status": "ok", "database": "connected"}
```

Se retornar erro, verifique os logs:
```bash
# No dashboard do Render
# lwksistemas-backup → Logs
```

### Passo 5: Configurar Failover no Frontend (3 min)

1. **Acesse:** https://vercel.com/

2. **Vá em:** Projeto `frontend` → Settings → Environment Variables

3. **Adicione:**
```
NEXT_PUBLIC_API_BACKUP_URL=https://lwksistemas-backup.onrender.com
```

4. **Clique em:** `Save`

5. **Faça deploy:**
```bash
cd frontend
vercel --prod
```

## ✅ Verificação Final

### Checklist

- [ ] Banco de dados criado no Render
- [ ] Dados copiados do Heroku
- [ ] Variáveis configuradas no Render
- [ ] Deploy concluído com sucesso
- [ ] Health check respondendo OK
- [ ] Variável de backup configurada no Vercel

### Testes

```bash
# 1. Testar API principal (Heroku)
curl https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/health/

# 2. Testar API backup (Render)
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/

# 3. Testar autenticação
curl -X POST https://lwksistemas-backup.onrender.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

## 🔄 Sincronização de Dados

### Configurar Sincronização Diária

Para manter os dados atualizados, configure sincronização automática:

1. **Criar script de sincronização:**

```bash
# scripts/sync_heroku_to_render.sh
#!/bin/bash
heroku pg:backups:capture --app lwksistemas
heroku pg:backups:download --app lwksistemas -o /tmp/backup.dump
pg_restore --clean --no-acl --no-owner \
  -d "$RENDER_DATABASE_URL" \
  /tmp/backup.dump
rm /tmp/backup.dump
```

2. **Agendar no Heroku Scheduler:**

```bash
# Instalar addon
heroku addons:create scheduler:standard --app lwksistemas

# Abrir painel
heroku addons:open scheduler --app lwksistemas

# Adicionar job:
# Frequência: Daily (todo dia às 2h da manhã)
# Comando: ./scripts/sync_heroku_to_render.sh
```

## 📊 Monitoramento

### Logs do Render

```bash
# Ver logs em tempo real
# Dashboard → lwksistemas-backup → Logs
```

### Métricas

```bash
# Dashboard → lwksistemas-backup → Metrics
# - CPU Usage
# - Memory Usage
# - Response Time
```

### Alertas

Configure alertas no Render:
- Deploy failures
- High error rate
- High response time

## 🆘 Troubleshooting

### Erro: "Connection refused"
```bash
# Verificar se DATABASE_URL tem SSL
# Deve terminar com: ?sslmode=require
```

### Erro: "Authentication failed"
```bash
# Verificar se a DATABASE_URL está correta
# Copiar novamente do painel do Render
```

### Erro: "No module named 'X'"
```bash
# Verificar requirements.txt
# Fazer rebuild: Dashboard → Manual Deploy → Deploy Latest Commit
```

## 🎉 Conclusão

Servidor de backup configurado com sucesso!

**Arquitetura Final:**
```
Frontend (Vercel)
    ↓
    ├─→ Heroku (Principal) → AWS RDS
    └─→ Render (Backup) → Render PostgreSQL
```

**Próximos passos:**
- ✅ Monitorar logs regularmente
- ✅ Testar failover mensalmente
- ✅ Verificar sincronização de dados
- ✅ Configurar alertas

## 📚 Documentação

- **Análise Completa:** `ANALISE_SERVIDOR_BACKUP_RENDER.md`
- **Correção de Erros:** `CORRECAO_ERRO_RENDER_DATABASE.md`
- **Scripts:** `scripts/setup_render_database.sh`
