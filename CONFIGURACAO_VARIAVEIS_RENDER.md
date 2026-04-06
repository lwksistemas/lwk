# Configuração de Variáveis de Ambiente - Render

## 📅 Data
06/04/2026

## 🎯 Objetivo

Documentar a configuração correta de todas as variáveis de ambiente necessárias para o servidor Render (`lwksistemas-backup`).

## ⚠️ IMPORTANTE

**NÃO inclua o nome da variável no valor!**

❌ **ERRADO:**
```
Key: CORS_ALLOWED_ORIGINS
Value: CORS_ALLOWED_ORIGINS=https://lwksistemas.com.br
```

✅ **CORRETO:**
```
Key: CORS_ALLOWED_ORIGINS
Value: https://lwksistemas.com.br,https://www.lwksistemas.com.br
```

## 📋 Variáveis Obrigatórias

### 1. DATABASE_URL
**Descrição:** URL de conexão com o banco de dados PostgreSQL do Render

**Formato:**
```
postgresql://[usuario]:[senha]@[host]:[porta]/[database]?sslmode=require
```

**Exemplo:**
```
postgresql://lwksistemas_user:abc123xyz@dpg-xxxxx.oregon-postgres.render.com:5432/lwksistemas_db?sslmode=require
```

**Como obter:**
1. Dashboard Render → Seu banco PostgreSQL
2. Copiar "Internal Database URL"
3. Adicionar `?sslmode=require` no final

**⚠️ IMPORTANTE:** Sempre adicione `?sslmode=require` no final!

---

### 2. SECRET_KEY
**Descrição:** Chave secreta do Django (DEVE ser a mesma do Heroku para tokens JWT funcionarem)

**Como obter do Heroku:**
```bash
heroku config:get SECRET_KEY --app lwksistemas
```

**Formato:**
```
django-insecure-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**⚠️ CRÍTICO:** Use EXATAMENTE a mesma SECRET_KEY do Heroku! Caso contrário, tokens JWT não funcionarão entre servidores.

---

### 3. ALLOWED_HOSTS
**Descrição:** Hosts permitidos para acessar a aplicação

**Valor:**
```
lwksistemas-backup.onrender.com,.onrender.com,lwksistemas.com.br,www.lwksistemas.com.br
```

**Explicação:**
- `lwksistemas-backup.onrender.com` - URL do serviço Render
- `.onrender.com` - Qualquer subdomínio do Render
- `lwksistemas.com.br` - Domínio principal
- `www.lwksistemas.com.br` - Domínio com www

---

### 4. CORS_ALLOWED_ORIGINS
**Descrição:** Origens permitidas para requisições CORS

**Valor:**
```
https://lwksistemas.com.br,https://www.lwksistemas.com.br
```

**⚠️ ATENÇÃO:** 
- Use vírgula (`,`) para separar múltiplas origens
- Sempre inclua `https://` no início
- NÃO adicione espaços entre as URLs
- NÃO inclua o nome da variável no valor

---

### 5. DJANGO_SETTINGS_MODULE
**Descrição:** Módulo de configurações do Django

**Valor:**
```
config.settings
```

---

### 6. DEBUG
**Descrição:** Modo de debug (SEMPRE False em produção)

**Valor:**
```
False
```

---

### 7. ENVIRONMENT
**Descrição:** Ambiente de execução

**Valor:**
```
production
```

---

## 📋 Variáveis Opcionais (mas Recomendadas)

### 8. CORS_ALLOW_ALL_ORIGINS
**Descrição:** Permitir todas as origens (use apenas para testes)

**Valor para produção:**
```
False
```

**Valor para testes (temporário):**
```
True
```

**⚠️ SEGURANÇA:** Em produção, sempre use `False` e configure `CORS_ALLOWED_ORIGINS` corretamente.

---

### 9. PYTHON_VERSION
**Descrição:** Versão do Python a ser usada

**Valor:**
```
3.12.0
```

---

### 10. WEB_CONCURRENCY
**Descrição:** Número de workers do Gunicorn (Render define automaticamente)

**Valor sugerido:**
```
2
```

**Nota:** Render define automaticamente baseado nas CPUs disponíveis. Só configure se necessário.

---

## 🔐 Variáveis de Integração (se aplicável)

### 11. ASAAS_API_KEY
**Descrição:** Chave de API do Asaas (gateway de pagamento)

**Como obter:**
1. Painel Asaas → Integrações → API Key
2. Copiar a chave

**Formato:**
```
$aact_YTU5YTE0M2M2N2I4MTliNzk0YTI5N2U5MzdjNWZmNDQ6OjAwMDAwMDAwMDAwMDAwMDAwMDA6OiRhYWNoXzAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMA==
```

---

### 12. GOOGLE_CLIENT_ID
**Descrição:** Client ID do Google OAuth (se usar login com Google)

**Como obter:**
1. Google Cloud Console → APIs & Services → Credentials
2. Copiar Client ID

---

### 13. GOOGLE_CLIENT_SECRET
**Descrição:** Client Secret do Google OAuth

**Como obter:**
1. Google Cloud Console → APIs & Services → Credentials
2. Copiar Client Secret

---

## 📝 Passo a Passo para Configurar

### 1. Acessar Dashboard do Render

1. Acesse: https://dashboard.render.com
2. Faça login
3. Selecione o serviço `lwksistemas-backup`

### 2. Acessar Configurações de Ambiente

1. No menu lateral esquerdo, clique em **Environment**
2. Você verá a lista de variáveis de ambiente

### 3. Adicionar/Editar Variáveis

Para cada variável:

1. Clique em **Add Environment Variable** (ou edite existente)
2. Preencha:
   - **Key:** Nome da variável (ex: `CORS_ALLOWED_ORIGINS`)
   - **Value:** Valor da variável (ex: `https://lwksistemas.com.br,https://www.lwksistemas.com.br`)
3. Clique em **Save**

### 4. Salvar e Fazer Redeploy

1. Após adicionar/editar todas as variáveis, clique em **Save Changes**
2. Render fará redeploy automaticamente
3. Aguarde 2-3 minutos para o deploy completar

---

## ✅ Checklist de Configuração

Use este checklist para garantir que tudo está configurado:

- [ ] `DATABASE_URL` - Com `?sslmode=require` no final
- [ ] `SECRET_KEY` - Mesma do Heroku
- [ ] `ALLOWED_HOSTS` - Inclui `.onrender.com` e domínios
- [ ] `CORS_ALLOWED_ORIGINS` - URLs com `https://`, sem espaços
- [ ] `DJANGO_SETTINGS_MODULE` - `config.settings`
- [ ] `DEBUG` - `False`
- [ ] `ENVIRONMENT` - `production`
- [ ] `CORS_ALLOW_ALL_ORIGINS` - `False` (ou removida)
- [ ] Nenhuma variável tem o nome incluído no valor
- [ ] Deploy completou com sucesso
- [ ] Health check retorna 200 OK

---

## 🧪 Como Testar

### 1. Verificar Health Check

```bash
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-04-06T..."
}
```

### 2. Verificar CORS

No navegador, abra o console (F12) e execute:

```javascript
fetch('https://lwksistemas-backup.onrender.com/api/superadmin/health/')
  .then(r => r.json())
  .then(d => console.log('✅ CORS OK:', d))
  .catch(e => console.error('❌ CORS Error:', e))
```

**Resultado esperado:** `✅ CORS OK: {status: "healthy", ...}`

### 3. Testar Troca de Servidor

1. Acesse: https://lwksistemas.com.br/superadmin/dashboard
2. Clique no botão de servidor (canto superior direito)
3. Selecione "Render"
4. Aguarde o modal de "Acordando servidor..."
5. Sistema deve trocar com sucesso

---

## 🐛 Troubleshooting

### Erro: "CORS_ALLOWED_ORIGINS não possui esquema"

**Causa:** Valor da variável inclui o nome da variável

**Solução:**
```
❌ ERRADO: CORS_ALLOWED_ORIGINS=https://lwksistemas.com.br
✅ CORRETO: https://lwksistemas.com.br,https://www.lwksistemas.com.br
```

### Erro: "No 'Access-Control-Allow-Origin' header"

**Causa:** CORS não configurado corretamente

**Solução:**
1. Verificar `CORS_ALLOWED_ORIGINS` tem as URLs corretas
2. Verificar `ALLOWED_HOSTS` inclui os domínios
3. Temporariamente, testar com `CORS_ALLOW_ALL_ORIGINS=True`

### Erro: "Nenhuma sessão ativa encontrada"

**Causa:** SECRET_KEY diferente do Heroku

**Solução:**
1. Obter SECRET_KEY do Heroku: `heroku config:get SECRET_KEY --app lwksistemas`
2. Configurar EXATAMENTE a mesma no Render
3. Fazer redeploy

### Erro: "SSL connection required"

**Causa:** DATABASE_URL sem `?sslmode=require`

**Solução:**
1. Adicionar `?sslmode=require` no final da DATABASE_URL
2. Fazer redeploy

---

## 📊 Exemplo Completo de Configuração

```
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
SECRET_KEY=django-insecure-abc123xyz...
ALLOWED_HOSTS=lwksistemas-backup.onrender.com,.onrender.com,lwksistemas.com.br,www.lwksistemas.com.br
CORS_ALLOWED_ORIGINS=https://lwksistemas.com.br,https://www.lwksistemas.com.br
DJANGO_SETTINGS_MODULE=config.settings
DEBUG=False
ENVIRONMENT=production
CORS_ALLOW_ALL_ORIGINS=False
PYTHON_VERSION=3.12.0
```

---

## 🔄 Sincronização com Heroku

Para manter as configurações sincronizadas entre Heroku e Render:

### Listar variáveis do Heroku:
```bash
heroku config --app lwksistemas
```

### Copiar variável específica:
```bash
heroku config:get SECRET_KEY --app lwksistemas
heroku config:get ASAAS_API_KEY --app lwksistemas
```

### Variáveis que DEVEM ser iguais:
- `SECRET_KEY` - Para tokens JWT funcionarem
- `ASAAS_API_KEY` - Para pagamentos funcionarem
- `GOOGLE_CLIENT_ID` - Para login Google funcionar
- `GOOGLE_CLIENT_SECRET` - Para login Google funcionar

### Variáveis que DEVEM ser diferentes:
- `DATABASE_URL` - Cada servidor tem seu próprio banco
- `ALLOWED_HOSTS` - Inclui hosts específicos de cada servidor

---

## 📚 Referências

- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Django CORS Headers](https://github.com/adamchainz/django-cors-headers)
- [Django Settings](https://docs.djangoproject.com/en/4.2/ref/settings/)
- [PostgreSQL SSL Mode](https://www.postgresql.org/docs/current/libpq-ssl.html)

---

## ✅ Status

**Última atualização:** 06/04/2026

**Próximos passos:**
1. Corrigir `CORS_ALLOWED_ORIGINS` no Render
2. Aguardar redeploy automático
3. Testar health check
4. Testar troca de servidor no frontend
