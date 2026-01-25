# 🚀 DEPLOY - CORREÇÃO SESSÃO ÚNICA

## ✅ Backend Deployado (Heroku)

**Commit:** `938f2b7`
**Mensagem:** "fix: Corrigir sessão única - impedir refresh quando DIFFERENT_SESSION + logs detalhados"

### Mudanças no Backend:

1. **session_manager.py** - Logs detalhados ao criar sessão
   - Mostra quando sessão anterior é deletada
   - Mostra hash do token para debug
   - Logs em WARNING para aparecer no Heroku

## 🔧 Frontend - PRECISA DEPLOY NO VERCEL

### Mudanças no Frontend:

**Arquivo:** `frontend/lib/api-client.ts`

**Correção Crítica:**
- Antes: Tentava refresh token ANTES de verificar erro de sessão
- Depois: Verifica erro de sessão PRIMEIRO, só tenta refresh se não for erro de sessão

**Comportamento Corrigido:**
```typescript
// ANTES (BUGADO):
1. Recebe 401 DIFFERENT_SESSION
2. Tenta refresh token (cria nova sessão, invalida a outra)
3. Loop infinito de refresh entre dispositivos

// DEPOIS (CORRETO):
1. Recebe 401 DIFFERENT_SESSION
2. Faz logout IMEDIATO (sem tentar refresh)
3. Mostra mensagem: "Outra sessão foi iniciada em outro dispositivo"
4. Redireciona para home
```

## 📋 Como Fazer Deploy do Frontend

### Opção 1: Deploy Automático (Vercel + GitHub)

Se o frontend está conectado ao GitHub:
```bash
# Fazer push para o repositório
git push origin master
```

Vercel vai detectar e fazer deploy automático.

### Opção 2: Deploy Manual (Vercel CLI)

```bash
cd frontend
vercel --prod
```

### Opção 3: Deploy via Dashboard Vercel

1. Acesse https://vercel.com/dashboard
2. Encontre o projeto `lwksistemas`
3. Clique em "Deployments"
4. Clique em "Redeploy" no último deployment

## 🧪 Como Testar Após Deploy

### Teste 1: Login Único Funciona

1. **Dispositivo A (Desktop):**
   - Fazer login com usuário `luiz`
   - Acessar dashboard
   - ✅ Deve funcionar normalmente

2. **Dispositivo B (Mobile):**
   - Fazer login com MESMO usuário `luiz`
   - ✅ Deve fazer login com sucesso

3. **Dispositivo A (Desktop):**
   - Tentar acessar qualquer página
   - ❌ Deve receber erro: "Outra sessão foi iniciada em outro dispositivo"
   - ✅ Deve ser deslogado automaticamente
   - ✅ Deve redirecionar para home

### Teste 2: Não Permite Uso Simultâneo

1. **Desktop:** Login com `luiz`
2. **Mobile:** Login com `luiz` (invalida desktop)
3. **Desktop:** Tenta acessar → Deslogado ✅
4. **Mobile:** Continua funcionando ✅

### Teste 3: Logs Detalhados

Verificar logs do Heroku:
```bash
heroku logs --tail --app lwksistemas
```

Deve mostrar:
```
🔐 CRIANDO NOVA SESSÃO para usuário 1
⚠️ SESSÃO ANTERIOR DETECTADA para usuário 1
🗑️ 1 sessão(ões) anterior(es) DELETADA(S)
✅ NOVA SESSÃO CRIADA no banco
```

## 🔍 Verificar se Funcionou

### No Console do Browser (F12):

Quando receber erro de sessão, deve aparecer:
```
🔍 Erro 401 detectado: { errorCode: 'DIFFERENT_SESSION', errorMessage: '...' }
🚨 SESSÃO INVÁLIDA - Fazendo logout forçado: DIFFERENT_SESSION
```

### No Heroku Logs:

Quando criar nova sessão:
```
🔐 CRIANDO NOVA SESSÃO para usuário X
⚠️ SESSÃO ANTERIOR DETECTADA
🗑️ DELETANDO sessão anterior
✅ NOVA SESSÃO CRIADA
```

## ⚠️ IMPORTANTE

**Após o deploy do frontend, o sistema vai:**

1. ✅ Permitir apenas 1 sessão por usuário
2. ✅ Invalidar sessão anterior ao fazer novo login
3. ✅ Deslogar automaticamente quando detectar outra sessão
4. ✅ Mostrar mensagem clara ao usuário
5. ✅ Não permitir uso simultâneo em múltiplos dispositivos

## 🎯 Resultado Esperado

**ANTES (Bugado):**
- Usuário conseguia usar 2 dispositivos simultaneamente
- Refresh token criava loop infinito
- Sessões ficavam alternando

**DEPOIS (Correto):**
- Usuário só pode usar 1 dispositivo por vez
- Login em novo dispositivo = logout automático no anterior
- Mensagem clara: "Outra sessão foi iniciada em outro dispositivo"

---

**Data:** 25/01/2026 23:15
**Status Backend:** ✅ DEPLOYADO
**Status Frontend:** ⏳ AGUARDANDO DEPLOY
**Versão:** v224
