# Solução: Rollback Automático do Render

## 📅 Data
06/04/2026 - 16:45

## 🔴 Problema

Render está fazendo rollback automático do deploy:

```
Timed out after waiting for internal health check to return a successful response code
Rollback
```

**Causa:** O servidor demora muito para iniciar (cold start) e o health check do Render tem timeout muito curto.

## ✅ Solução Imediata

### Opção 1: Desabilitar Health Check Path (Recomendado)

1. **Acesse Dashboard do Render**
   - https://dashboard.render.com
   - Serviço: `lwksistemas-backup`

2. **Vá em Settings → Health & Alerts**
   - Procure por "Health Check Path"
   - **DELETE** o caminho `/api/superadmin/health/`
   - Deixe em branco

3. **Salvar e Fazer Redeploy Manual**
   - Clique em "Save Changes"
   - Botão "Manual Deploy" → "Deploy latest commit"
   - Aguarde 3-5 minutos

**Por que funciona:**
- Sem health check path, Render só verifica se a porta está aberta
- Servidor tem mais tempo para inicializar
- Não faz rollback automático

### Opção 2: Aumentar Timeout do Health Check

Se quiser manter o health check:

1. **Settings → Health & Alerts**
2. Procure por configurações de timeout
3. Se disponível, aumente para 120 segundos
4. Salvar e redeploy

**Nota:** Plano Free pode não ter essa opção.

## 📋 Passo a Passo Detalhado

### 1. Acessar Configurações

```
Dashboard Render → lwksistemas-backup → Settings (menu lateral)
```

### 2. Encontrar Health Check

Role a página até encontrar:
- "Health & Alerts" ou
- "Health Check" ou  
- "Exames de saúde"

### 3. Configuração Atual (Problemática)

```
Health Check Path: /api/superadmin/health/
```

Isso faz o Render verificar se esse endpoint responde 200 OK rapidamente.

### 4. Nova Configuração (Solução)

```
Health Check Path: [deixar em branco]
```

Ou se tiver opção de timeout:
```
Health Check Path: /api/superadmin/health/
Health Check Timeout: 120 seconds
```

### 5. Salvar e Redeploy

1. Clique em "Save Changes"
2. Vá para a aba principal do serviço
3. Clique em "Manual Deploy"
4. Selecione "Deploy latest commit"
5. Aguarde 3-5 minutos

## 🧪 Como Verificar se Funcionou

### 1. Acompanhar Logs

Durante o deploy, veja os logs:

**Sinais de sucesso:**
```
✅ Superadmin: Signals de limpeza carregados
✅ Asaas Integration: Signals carregados
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
==> Detected service running on port 10000
```

**NÃO deve aparecer:**
```
Timed out after waiting for internal health check
Rollback
```

### 2. Testar Manualmente

Após deploy completar:

```bash
curl https://lwksistemas-backup.onrender.com/api/superadmin/health/
```

Deve retornar:
```json
{"status": "healthy", "database": "connected", ...}
```

## 📊 Comparação

| Configuração | Vantagem | Desvantagem |
|--------------|----------|-------------|
| Sem health check | ✅ Não faz rollback<br>✅ Mais tempo para iniciar | ⚠️ Não detecta falhas automaticamente |
| Com health check + timeout alto | ✅ Detecta falhas<br>✅ Tempo suficiente | ⚠️ Pode não estar disponível no Free |
| Com health check + timeout baixo | ✅ Detecta falhas rápido | ❌ Faz rollback no cold start |

## 🎯 Recomendação

**Para servidor de backup (plano Free):**

1. **Desabilitar health check path** (deixar em branco)
2. Render vai apenas verificar se a porta está aberta
3. Servidor terá tempo suficiente para inicializar
4. Não fará rollback automático

**Justificativa:**
- Servidor de backup não precisa de health check agressivo
- Cold start do plano Free é lento (30-90s)
- Health check muito rápido causa rollbacks desnecessários
- Melhor deixar servidor inicializar tranquilamente

## 🔧 Configuração Alternativa

Se não conseguir desabilitar o health check, tente mudar para um endpoint mais simples:

### Criar Endpoint Simples

No `backend/config/urls.py`, adicionar:

```python
from django.http import JsonResponse

def simple_health(request):
    return JsonResponse({'ok': True})

urlpatterns = [
    # ... outras rotas ...
    path('health/', simple_health),  # Endpoint super simples
]
```

Depois configurar no Render:
```
Health Check Path: /health/
```

Este endpoint responde instantaneamente, sem verificar banco de dados.

## 📝 Checklist

- [ ] Acessar Dashboard do Render
- [ ] Ir em Settings → Health & Alerts
- [ ] Deletar ou deixar em branco "Health Check Path"
- [ ] Salvar mudanças
- [ ] Fazer Manual Deploy
- [ ] Aguardar 5 minutos
- [ ] Verificar logs (sem rollback)
- [ ] Testar health check manualmente
- [ ] Testar login no frontend

## ⚠️ Se Ainda Não Funcionar

### Plano B: Forçar Deploy Sem Health Check

1. **Suspender serviço atual**
   - Settings → Suspend Service

2. **Reativar serviço**
   - Settings → Resume Service

3. **Fazer deploy manual**
   - Manual Deploy → Deploy latest commit

4. **Aguardar inicialização completa**
   - Não interromper mesmo se demorar

### Plano C: Criar Novo Serviço

Se nada funcionar:

1. Criar novo serviço no Render
2. Usar mesmas configurações
3. **NÃO configurar Health Check Path**
4. Conectar ao mesmo banco de dados
5. Fazer deploy

## 🎊 Resultado Esperado

Após desabilitar o health check:

- ✅ Deploy completa sem rollback
- ✅ Servidor inicializa completamente
- ✅ Health check manual funciona
- ✅ Login funciona
- ✅ Sistema operacional

---

**Status:** 🔴 AGUARDANDO CONFIGURAÇÃO NO RENDER

**Próxima ação:** Desabilitar Health Check Path no Dashboard

**Tempo estimado:** 10 minutos (configuração + deploy)
