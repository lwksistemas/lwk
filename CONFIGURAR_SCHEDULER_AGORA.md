# ⚡ Configurar Heroku Scheduler AGORA

O dashboard do Heroku Scheduler foi aberto no seu navegador!

## 📋 Siga estes passos:

### 1. No dashboard que abriu, clique no botão **"Create job"**

### 2. Preencha o formulário:

**Job command:**
```
cd backend && python manage.py detect_security_violations
```

**Schedule:**
- Selecione: **"Every 10 minutes"**

**Dyno size:**
- Selecione: **"Standard-1X"** (ou o mesmo tipo usado pela aplicação)

### 3. Clique em **"Save Job"**

## ✅ Pronto!

O sistema agora vai executar a detecção de violações automaticamente a cada 10 minutos.

## 🧪 Testar agora:

```bash
# Executar detecção manualmente
heroku run "cd backend && python manage.py detect_security_violations" -a lwksistemas

# Verificar status do sistema
heroku run "cd backend && python manage.py security_status" -a lwksistemas
```

## 📊 Monitorar:

```bash
# Ver logs do scheduler
heroku logs --tail --ps scheduler -a lwksistemas

# Acessar dashboard de alertas
# https://lwksistemas.com.br/superadmin/dashboard/alertas
```
