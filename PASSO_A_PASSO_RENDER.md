# 🚀 Passo a Passo: Configurar Render (Servidor Backup)

## Método Recomendado: Via Dashboard (Visual e Fácil)

---

## Passo 1: Criar Conta no Render

1. Acesse: **https://render.com**
2. Clique em **"Get Started"** ou **"Sign Up"**
3. Escolha **"Sign in with GitHub"**
4. Autorize o Render a acessar sua conta GitHub
5. ✅ Conta criada!

---

## Passo 2: Conectar Repositório

1. No dashboard do Render, clique em **"New +"** (canto superior direito)
2. Selecione **"Web Service"**
3. Você verá uma lista de repositórios do GitHub
4. Procure por **"lwksistemas"**
5. Clique em **"Connect"** ao lado do repositório

**Se o repositório não aparecer:**
- Clique em **"Configure account"**
- Autorize acesso ao repositório `lwksistemas`
- Volte e clique em **"Connect"**

---

## Passo 3: Configurar o Web Service

### 3.1. Informações Básicas

Preencha os campos:

| Campo | Valor |
|-------|-------|
| **Name** | `lwksistemas-backup` |
| **Region** | `Oregon (US West)` |
| **Branch** | `master` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |

### 3.2. Build & Deploy

| Campo | Valor |
|-------|-------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

### 3.3. Plano

- Selecione: **Free** ($0/mês)
- ⚠️ **Importante**: Free tier "dorme" após 15 minutos de inatividade
- Primeira requisição após "acordar" pode levar 30-60 segundos

---

## Passo 4: Configurar Variáveis de Ambiente

**IMPORTANTE**: Você precisa copiar TODAS as variáveis do Heroku!

### 4.1. Obter Variáveis do Heroku

Abra um terminal e execute:

```bash
heroku config -a lwksistemas
```

Você verá algo assim:

```
=== lwksistemas Config Vars
ALLOWED_HOSTS:              lwksistemas-38ad47519238.herokuapp.com
ASAAS_API_KEY:              $aact_YTU5YTE0M2M2N2I4...
DATABASE_URL:               postgres://u7abc123:p4ssw0rd@ec2-...
DEBUG:                      False
REDIS_URL:                  redis://h:p1234567890@ec2-...
SECRET_KEY:                 django-insecure-abc123...
...
```

### 4.2. Adicionar no Render

No Render, role até **"Environment Variables"** e adicione:

#### Variáveis Obrigatórias:

1. **DATABASE_URL**
   - Value: `[copie do Heroku]`
   - ⚠️ Deve ser a mesma URL do PostgreSQL do Heroku

2. **SECRET_KEY**
   - Value: `[copie do Heroku]`
   - ⚠️ Deve ser a mesma chave do Heroku

3. **DEBUG**
   - Value: `False`

4. **ALLOWED_HOSTS**
   - Value: `lwksistemas.onrender.com,lwksistemas-38ad47519238.herokuapp.com`
   - ⚠️ Adicione a URL do Render aqui

5. **CORS_ALLOWED_ORIGINS**
   - Value: `https://lwksistemas.com.br`

6. **REDIS_URL**
   - Value: `[copie do Heroku]`

7. **ASAAS_API_KEY**
   - Value: `[copie do Heroku]`

8. **ASAAS_WEBHOOK_SECRET**
   - Value: `[copie do Heroku]`

9. **MERCADOPAGO_ACCESS_TOKEN**
   - Value: `[copie do Heroku]`

10. **MERCADOPAGO_PUBLIC_KEY**
    - Value: `[copie do Heroku]`

11. **EMAIL_HOST**
    - Value: `[copie do Heroku]`

12. **EMAIL_PORT**
    - Value: `[copie do Heroku]`

13. **EMAIL_HOST_USER**
    - Value: `[copie do Heroku]`

14. **EMAIL_HOST_PASSWORD**
    - Value: `[copie do Heroku]`

15. **EMAIL_USE_TLS**
    - Value: `True`

16. **DEFAULT_FROM_EMAIL**
    - Value: `[copie do Heroku]`

#### Como Adicionar Cada Variável:

1. Clique em **"Add Environment Variable"**
2. Digite o **Key** (nome da variável)
3. Cole o **Value** (valor copiado do Heroku)
4. Clique em **"Add"**
5. Repita para todas as variáveis

---

## Passo 5: Deploy

1. Role até o final da página
2. Clique em **"Create Web Service"**
3. ⏳ Aguarde o deploy (5-10 minutos)
4. Você verá os logs em tempo real

### Logs Esperados:

```
==> Cloning from https://github.com/seu-usuario/lwksistemas...
==> Checking out commit abc123...
==> Running build command 'pip install -r requirements.txt'...
==> Installing dependencies...
==> Build successful!
==> Starting service with 'gunicorn config.wsgi:application'...
==> Your service is live 🎉
```

---

## Passo 6: Verificar URL do Render

Após o deploy, você verá a URL do seu serviço:

```
https://lwksistemas-backup.onrender.com
```

⚠️ **Anote esta URL!** Você vai precisar dela no próximo passo.

---

## Passo 7: Testar o Servidor Backup

Abra um terminal e teste:

```bash
# Testar health check
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
```

**Resposta esperada:**

```json
{
  "status": "healthy",
  "database": "connected",
  "lojas_count": 4,
  "timestamp": "2026-02-27T12:00:00.000000+00:00",
  "version": "v750"
}
```

✅ Se você viu isso, o servidor backup está funcionando!

---

## Passo 8: Configurar Variáveis no Vercel

Agora você precisa informar ao frontend sobre o servidor backup.

### 8.1. Via Dashboard do Vercel (Recomendado)

1. Acesse: **https://vercel.com/lwks-projects-48afd555/frontend/settings/environment-variables**
2. Clique em **"Add New"**
3. Adicione as variáveis:

**Variável 1:**
- **Key**: `NEXT_PUBLIC_API_BACKUP_URL`
- **Value**: `https://lwksistemas-backup.onrender.com`
- **Environment**: Marque apenas **Production**
- Clique em **"Save"**

**Variável 2:**
- **Key**: `NEXT_PUBLIC_API_TIMEOUT`
- **Value**: `20000`
- **Environment**: Marque apenas **Production**
- Clique em **"Save"**

### 8.2. Redeploy do Frontend

Após adicionar as variáveis, você precisa fazer redeploy:

**Opção A: Via Dashboard**
1. Vá em **"Deployments"**
2. Clique nos 3 pontinhos do último deploy
3. Clique em **"Redeploy"**
4. Confirme

**Opção B: Via Terminal**
```bash
cd frontend
vercel --prod
```

---

## Passo 9: Testar o Failover

### 9.1. Verificar que está funcionando normalmente

1. Acesse: **https://lwksistemas.com.br/superadmin/dashboard**
2. Faça login
3. Abra o **Console do Navegador** (F12)
4. Navegue pelo sistema
5. Você deve ver requisições para o Heroku funcionando normalmente

### 9.2. Simular falha do Heroku

```bash
# Desligar o Heroku temporariamente
heroku ps:scale web=0 -a lwksistemas
```

### 9.3. Testar failover

1. Recarregue a página: **https://lwksistemas.com.br/superadmin/dashboard**
2. Tente fazer login ou navegar
3. Observe o console do navegador:

**Você deve ver:**
```
⚠️ API primária falhou (ERR_NETWORK), tentando backup (1/3)...
🔄 Repetindo requisição no servidor backup...
API Response: 200 /api/superadmin/lojas/
```

4. ✅ O sistema deve continuar funcionando normalmente!

### 9.4. Reativar Heroku

```bash
# Ligar o Heroku novamente
heroku ps:scale web=1 -a lwksistemas
```

### 9.5. Verificar recuperação automática

1. Continue usando o sistema normalmente
2. Após **5 minutos**, o sistema deve voltar automaticamente para o Heroku
3. No console você verá:
```
✅ Voltando para API primária após 5 minutos de sucesso
```

---

## Troubleshooting

### ❌ Erro: "Application failed to respond"

**Causa**: Variáveis de ambiente incorretas ou faltando

**Solução**:
1. Vá em **Settings** → **Environment Variables**
2. Verifique se TODAS as variáveis do Heroku foram copiadas
3. Especialmente: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`
4. Clique em **"Manual Deploy"** → **"Deploy latest commit"**

### ❌ Erro: "Database connection failed"

**Causa**: PostgreSQL do Heroku não aceita conexão do Render

**Solução**:
1. O PostgreSQL do Heroku deve aceitar conexões externas (geralmente aceita)
2. Verifique se a `DATABASE_URL` está correta
3. Se necessário, adicione o IP do Render à whitelist do PostgreSQL

### ❌ Erro: "CORS error"

**Causa**: URL do Render não está no `CORS_ALLOWED_ORIGINS`

**Solução**:
1. No Render, vá em **Environment Variables**
2. Edite `CORS_ALLOWED_ORIGINS`
3. Adicione: `https://lwksistemas.com.br,https://lwksistemas-backup.onrender.com`
4. Redeploy

### ❌ Failover não ativa

**Causa**: Variáveis não configuradas no Vercel

**Solução**:
1. Verifique se as variáveis foram adicionadas no Vercel
2. Verifique se fez redeploy após adicionar as variáveis
3. Limpe o cache do navegador (Ctrl+Shift+Delete)

### ⚠️ Render muito lento (primeira requisição)

**Causa**: Free tier "dorme" após 15 minutos de inatividade

**Soluções**:
1. **Aceitar o delay**: Primeira requisição leva 30-60s, depois fica rápido
2. **Upgrade para pago**: $7/mês, sem "sleep"
3. **Keep-alive service**: Fazer ping a cada 10 minutos (não recomendado)

---

## Checklist Final

- [ ] Conta criada no Render
- [ ] Repositório conectado
- [ ] Web Service criado com nome `lwksistemas-backup`
- [ ] Todas as variáveis de ambiente copiadas do Heroku
- [ ] `ALLOWED_HOSTS` inclui URL do Render
- [ ] Deploy concluído com sucesso
- [ ] Health check testado e funcionando
- [ ] Variável `NEXT_PUBLIC_API_BACKUP_URL` adicionada no Vercel
- [ ] Variável `NEXT_PUBLIC_API_TIMEOUT` adicionada no Vercel
- [ ] Redeploy do frontend realizado
- [ ] Teste de failover realizado com sucesso
- [ ] Heroku reativado
- [ ] Sistema voltou para Heroku após 5 minutos

---

## Comandos Úteis

```bash
# Ver variáveis do Heroku
heroku config -a lwksistemas

# Testar health do Heroku
curl https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/health/

# Testar health do Render
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/

# Desligar Heroku (teste)
heroku ps:scale web=0 -a lwksistemas

# Ligar Heroku
heroku ps:scale web=1 -a lwksistemas

# Ver logs do Heroku
heroku logs --tail -a lwksistemas

# Redeploy do Vercel
cd frontend && vercel --prod
```

---

## Resumo Visual

```
┌─────────────────────────────────────────────────────────┐
│  1. Criar conta no Render (GitHub)                      │
│  2. Conectar repositório lwksistemas                    │
│  3. Criar Web Service (Python, Free)                    │
│  4. Copiar TODAS variáveis do Heroku                    │
│  5. Deploy (aguardar 5-10 min)                          │
│  6. Testar: curl .../health/                            │
│  7. Adicionar variáveis no Vercel                       │
│  8. Redeploy do frontend                                │
│  9. Testar failover (desligar Heroku)                   │
│ 10. ✅ Sistema com redundância funcionando!             │
└─────────────────────────────────────────────────────────┘
```

---

## Tempo Estimado

- Criar conta e conectar: **2 minutos**
- Configurar service: **3 minutos**
- Copiar variáveis: **5 minutos**
- Deploy: **5-10 minutos** (automático)
- Configurar Vercel: **2 minutos**
- Testar: **5 minutos**

**Total: ~20-30 minutos**

---

## Suporte

Se tiver dúvidas em algum passo:
1. Verifique os logs do Render (aba "Logs")
2. Teste o health check
3. Verifique se todas as variáveis foram copiadas
4. Consulte a documentação: `IMPLEMENTACAO_FAILOVER_v750.md`

---

**Boa sorte! 🚀**

Após configurar, seu sistema terá redundância completa com custo zero adicional!
