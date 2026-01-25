# Teste de Sessão Única - v191

## 🎯 OBJETIVO DO TESTE

Verificar se o `SessionAwareJWTAuthentication` está sendo chamado e se está validando a blacklist corretamente.

## 📋 PASSO A PASSO

### 1. Fazer Login no Computador

1. Abrir https://lwksistemas.com.br no computador
2. Fazer login com:
   - Usuário: `luiz`
   - Senha: `147Luiz@`
3. Acessar o dashboard

### 2. Fazer Login no Celular

1. Abrir https://lwksistemas.com.br no celular
2. Fazer login com:
   - Usuário: `luiz`
   - Senha: `147Luiz@`
3. Acessar o dashboard

### 3. Tentar Usar o Computador Novamente

1. No computador, tentar navegar para qualquer página
2. Ou fazer qualquer requisição à API

## 🔍 O QUE OBSERVAR NOS LOGS

### Logs Esperados no Login do Celular:

```
🔥🔥🔥 CREATE_SESSION CHAMADO - Usuário 1
🚨🚨🚨 SESSÃO ANTERIOR DETECTADA - Usuário 1
✅✅✅ TOKEN ADICIONADO À BLACKLIST COM SUCESSO!
```

### Logs Esperados ao Usar o Computador Após Login no Celular:

**CENÁRIO 1: Authenticator está sendo chamado (ESPERADO)**
```
🔥🔥🔥 SessionAwareJWTAuthentication.authenticate() CHAMADO
   Path: /api/superadmin/lojas/estatisticas/
   Method: GET
   ✅ JWT válido para usuário: luiz (ID: 1)
   Token extraído (50 chars): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Token extraído (tamanho): 340 caracteres
   🔍 Chamando SessionManager.validate_session()...

🔍🔍🔍 VALIDATE_SESSION CHAMADO - Usuário 1
   Token recebido (50 chars): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Token recebido (tamanho): 340 caracteres
   🔍 Verificando blacklist...
   Hash do token: 6df4cd6adb60c07104d77a91dcf101dbd89fed40f69dc10d59cbbd946449c91d
   Chave blacklist: blacklist:6df4cd6adb60c07104d77a91dcf101dbd89fed40f69dc10d59cbbd946449c91d
   Está na blacklist? True

🚫🚫🚫 TOKEN NA BLACKLIST DETECTADO - Usuário 1
   Hash: 6df4cd6adb60c07104d77a91dcf101dbd89fed40f69dc10d59cbbd946449c91d
   BLOQUEANDO ACESSO AGORA!

🚨🚨🚨 SESSÃO INVÁLIDA - Bloqueando acesso!
   Usuário: luiz
   Motivo: BLACKLISTED
   Mensagem: Token foi invalidado por nova sessão
```

**CENÁRIO 2: Authenticator NÃO está sendo chamado (PROBLEMA)**
```
(Nenhum log de authenticator)
```

**CENÁRIO 3: Token não está na blacklist (PROBLEMA)**
```
🔥🔥🔥 SessionAwareJWTAuthentication.authenticate() CHAMADO
🔍🔍🔍 VALIDATE_SESSION CHAMADO - Usuário 1
   🔍 Verificando blacklist...
   Está na blacklist? False  ← PROBLEMA AQUI!
```

**CENÁRIO 4: Token tem tamanho diferente (PROBLEMA)**
```
🔥🔥🔥 SessionAwareJWTAuthentication.authenticate() CHAMADO
   Token extraído (tamanho): 150 caracteres  ← PROBLEMA! Deveria ser ~340
```

## 🎯 RESULTADO ESPERADO

### No Frontend (Computador):
- ❌ Erro 401 Unauthorized
- ❌ Mensagem: "Token foi invalidado por nova sessão"
- ❌ Redirecionamento para tela de login

### Nos Logs do Heroku:
- ✅ Authenticator sendo chamado
- ✅ validate_session sendo chamado
- ✅ Token na blacklist detectado
- ✅ Acesso bloqueado

## 📊 COMO VER OS LOGS

```bash
heroku logs --tail --app lwksistemas
```

Ou acessar: https://dashboard.heroku.com/apps/lwksistemas/logs

## 🔧 POSSÍVEIS PROBLEMAS E SOLUÇÕES

### Problema 1: Authenticator NÃO está sendo chamado

**Causa**: REST_FRAMEWORK não está usando nosso authenticator

**Solução**: Verificar `backend/config/settings.py`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'superadmin.authentication.SessionAwareJWTAuthentication',  # ← DEVE ESTAR AQUI
    ],
}
```

### Problema 2: Token não está na blacklist

**Causa**: Hash do token está diferente ao adicionar vs ao verificar

**Solução**: Verificar se estamos usando o mesmo token completo em ambos os casos

### Problema 3: Token tem tamanho diferente

**Causa**: `str(token)` não retorna o token JWT completo

**Solução**: Usar `str(token.token)` ou `token.access_token`

### Problema 4: Acesso não é bloqueado mesmo com token na blacklist

**Causa**: Exception não está sendo lançada corretamente

**Solução**: Verificar se `raise InvalidToken()` está sendo executado

---

**Status**: Aguardando teste do usuário
**Versão**: v191
**Data**: 2026-01-23
