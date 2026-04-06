# Correção Urgente - Erro 503 no Render

## 📅 Data
06/04/2026

## 🚨 Problema Atual

Servidor Render está retornando **503 Service Unavailable** devido a erro de configuração:

```
ERROS:
?: (corsheaders.E013) A origem 'CORS_ALLOWED_ORIGINS=https://lwksistemas.com.br' 
   em CORS_ALLOWED_ORIGINS não possui esquema ou localização de rede.
```

## 🔍 Causa

A variável de ambiente no Render está configurada INCORRETAMENTE:

❌ **ERRADO (atual):**
```
Key: CORS_ALLOWED_ORIGINS
Value: CORS_ALLOWED_ORIGINS=https://lwksistemas.com.br
```

O valor inclui o nome da variável, causando erro no Django.

## ✅ Solução Imediata

### Passo 1: Acessar Dashboard do Render

1. Acesse: https://dashboard.render.com
2. Faça login
3. Selecione o serviço: **lwksistemas-backup**

### Passo 2: Corrigir Variável de Ambiente

1. No menu lateral, clique em **Environment**
2. Procure a variável `CORS_ALLOWED_ORIGINS`
3. **DELETAR** esta variável (ela está errada)
4. Criar nova variável com nome correto

### Passo 3: Criar Variável Correta

O Django lê a variável `CORS_ORIGINS` (não `CORS_ALLOWED_ORIGINS`).

**Configuração correta:**

```
Key: CORS_ORIGINS
Value: https://lwksistemas.com.br,https://www.lwksistemas.com.br
```

**⚠️ IMPORTANTE:**
- Nome da variável: `CORS_ORIGINS` (sem `_ALLOWED`)
- Valor: Apenas as URLs, separadas por vírgula, SEM espaços
- NÃO inclua o nome da variável no valor

### Passo 4: Salvar e Aguardar Deploy

1. Clique em **Save Changes**
2. Render fará redeploy automático
3. Aguarde 2-3 minutos
4. Verifique os logs para confirmar que não há mais erros

## 📋 Todas as Variáveis Corretas

Para evitar confusão, aqui estão TODAS as variáveis que devem estar configuradas:

### 1. CORS_ORIGINS (não CORS_ALLOWED_ORIGINS!)
```
Key: CORS_ORIGINS
Value: https://lwksistemas.com.br,https://www.lwksistemas.com.br
```

### 2. ALLOWED_HOSTS
```
Key: ALLOWED_HOSTS
Value: lwksistemas-backup.onrender.com,.onrender.com,lwksistemas.com.br,www.lwksistemas.com.br
```

### 3. DATABASE_URL
```
Key: DATABASE_URL
Value: postgresql://[usuario]:[senha]@[host]:[porta]/[database]?sslmode=require
```

### 4. SECRET_KEY
```
Key: SECRET_KEY
Value: [copiar do Heroku: heroku config:get SECRET_KEY --app lwksistemas]
```

### 5. DJANGO_SETTINGS_MODULE
```
Key: DJANGO_SETTINGS_MODULE
Value: config.settings
```

### 6. DEBUG
```
Key: DEBUG
Value: False
```

### 7. ENVIRONMENT
```
Key: ENVIRONMENT
Value: production
```

## 🧪 Como Verificar se Funcionou

### 1. Verificar Logs do Deploy

No Dashboard do Render, vá em **Logs** e procure por:

✅ **Sucesso:**
```
✅ Superadmin: Sinais de limpeza carregados
✅ Integração Asaas: Sinais carregados
160 arquivos estáticos copiados
==> Build com sucesso 🎉
==> Implantando...
```

❌ **Erro (se ainda aparecer):**
```
Erro de verificação do sistema:
ERROS:
?: (corsheaders.E013) A origem '...' em CORS_ALLOWED_ORIGINS não possui esquema
```

### 2. Testar Health Check

Abra o terminal e execute:

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

### 3. Testar no Navegador

1. Acesse: https://lwksistemas.com.br/superadmin/login
2. Abra o Console (F12)
3. Tente trocar para servidor Render
4. Não deve mais aparecer erro 503

## 📊 Resumo da Correção

| Item | Antes (Errado) | Depois (Correto) |
|------|----------------|------------------|
| Nome da variável | `CORS_ALLOWED_ORIGINS` | `CORS_ORIGINS` |
| Valor | `CORS_ALLOWED_ORIGINS=https://...` | `https://lwksistemas.com.br,https://www.lwksistemas.com.br` |
| Status do servidor | 503 Service Unavailable | 200 OK |

## ⚠️ Por que o Nome da Variável é Diferente?

No arquivo `backend/config/settings.py`, o Django está configurado assim:

```python
CORS_ALLOWED_ORIGINS = config(
    'CORS_ORIGINS',  # ← Lê a variável CORS_ORIGINS
    default='http://localhost:3000,http://127.0.0.1:3000'
).split(',')
```

O Django lê a variável de ambiente `CORS_ORIGINS` e atribui ao setting `CORS_ALLOWED_ORIGINS`.

Por isso, no Render você deve criar a variável `CORS_ORIGINS` (não `CORS_ALLOWED_ORIGINS`).

## 🔄 Próximos Passos

Após corrigir:

1. ✅ Aguardar deploy completar (2-3 minutos)
2. ✅ Verificar logs (sem erros)
3. ✅ Testar health check (200 OK)
4. ✅ Testar troca de servidor no frontend
5. ✅ Confirmar que sistema funciona normalmente

## 📞 Se Ainda Não Funcionar

Se após a correção ainda houver problemas:

1. Verifique se o valor não tem espaços extras
2. Verifique se tem `https://` no início de cada URL
3. Verifique se as URLs estão separadas por vírgula (sem espaços)
4. Tente temporariamente adicionar `CORS_ALLOW_ALL_ORIGINS=True` para testar

## ✅ Checklist Final

- [ ] Deletar variável `CORS_ALLOWED_ORIGINS` (nome errado)
- [ ] Criar variável `CORS_ORIGINS` (nome correto)
- [ ] Valor: `https://lwksistemas.com.br,https://www.lwksistemas.com.br`
- [ ] Salvar mudanças
- [ ] Aguardar redeploy (2-3 min)
- [ ] Verificar logs (sem erros)
- [ ] Testar health check
- [ ] Testar no frontend

---

**Status:** 🔴 AGUARDANDO CORREÇÃO NO RENDER

**Prioridade:** 🚨 URGENTE

**Tempo estimado:** 5 minutos (correção) + 3 minutos (deploy)
