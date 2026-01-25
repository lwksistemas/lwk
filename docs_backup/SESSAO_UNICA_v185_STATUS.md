# Sistema de Sessão Única - v185

## ✅ DEPLOY CONCLUÍDO

**Versão Backend**: v185  
**Versão Frontend**: v173  
**Data**: 23/01/2026

---

## 🎯 OBJETIVO

Garantir que cada usuário tenha **APENAS 1 sessão ativa** por vez. Se o usuário fizer login em outro dispositivo, a sessão anterior deve ser **BLOQUEADA IMEDIATAMENTE**.

---

## 🔧 CORREÇÕES IMPLEMENTADAS (v185)

### Problema Anterior (v184)
- Usuário `luiz` conseguia usar o sistema simultaneamente no celular e computador
- Logs mostravam blacklist funcionando, mas acesso não era bloqueado
- **Causa**: Middleware não bloqueava consistentemente

### Solução (v185)

#### 1. Bloqueio Forçado
```python
# Middleware agora BLOQUEIA IMEDIATAMENTE qualquer sessão inválida
if not validation['valid']:
    logger.critical("🚨🚨🚨 BLOQUEANDO ACESSO")
    return JsonResponse({'error': 'Sessão inválida'}, status=401)
```

#### 2. Logs Detalhados
- Token recebido (50 primeiros + 50 últimos caracteres)
- Token salvo (50 primeiros + 50 últimos caracteres)
- Tamanho dos tokens
- Comparação byte a byte
- Hash SHA256 para blacklist

#### 3. Rotas Públicas Atualizadas
- `/api/auth/logout/` agora é pública (permite logout mesmo com sessão inválida)
- `/static/` adicionado às rotas públicas

---

## 🧪 COMO TESTAR

### Passo a Passo

1. **Limpar tudo primeiro**
   - Fazer logout no computador
   - Fazer logout no celular
   - Limpar cache do navegador (opcional)

2. **Login no Computador**
   - Acessar: https://lwksistemas.com.br
   - Login: `luiz`
   - Senha: `147Luiz@`
   - Navegar pelo sistema (clicar em menus, ver dashboard)

3. **Login no Celular**
   - Acessar: https://lwksistemas.com.br
   - Login: `luiz`
   - Senha: `147Luiz@`
   - ✅ Login deve funcionar normalmente

4. **Testar Bloqueio no Computador**
   - Voltar para o computador
   - Clicar em qualquer menu ou atualizar página
   - ✅ **DEVE APARECER ERRO**: "Você foi desconectado porque iniciou uma nova sessão em outro dispositivo"
   - ✅ **DEVE SER REDIRECIONADO** para tela de login

5. **Confirmar Celular Funcionando**
   - No celular, navegar pelo sistema
   - ✅ Deve funcionar normalmente

---

## 📊 LOGS ESPERADOS

### No Login do Celular
```
🚨 SESSÃO ANTERIOR DETECTADA - Usuário 1
🚫 Token anterior adicionado à blacklist para usuário 1
   Hash: 98b66e34633b47006a962ec4f35de83d...
✅ Nova sessão criada e SALVA para usuário 1
```

### Na Próxima Requisição do Computador
```
🔍 VALIDANDO SESSÃO - Usuário 1
   Token recebido (50 chars): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Token recebido (tamanho): 287 caracteres
   Verificando blacklist...
   Hash do token: 98b66e34633b47006a962ec4f35de83d...
   Está na blacklist? True
🚫🚫🚫 TOKEN NA BLACKLIST - Usuário 1
   ACESSO DEVE SER BLOQUEADO!
🚨🚨🚨 BLOQUEANDO ACESSO - Usuário luiz (ID: 1)
   Motivo: BLACKLISTED
   Path bloqueado: /api/superadmin/lojas/estatisticas/
```

### Como Ver os Logs
```bash
heroku logs --tail --app lwksistemas
```

Ou acessar: https://dashboard.heroku.com/apps/lwksistemas/logs

---

## 🔍 FLUXO TÉCNICO

### 1. Login (Novo Dispositivo)
```
1. Usuário faz login no celular
2. Sistema verifica se já existe sessão ativa
3. Se SIM:
   - Calcula hash SHA256 do token antigo
   - Adiciona hash à blacklist no Redis (TTL: 1 hora)
   - Log: "🚫 Token anterior adicionado à blacklist"
4. Cria nova sessão com novo token
5. Salva no Redis: user_session:1 = {token, timestamp}
```

### 2. Requisição (Dispositivo Antigo)
```
1. Computador faz requisição com token antigo
2. Middleware extrai token do header Authorization
3. Calcula hash SHA256 do token
4. Verifica no Redis: blacklist:<hash>
5. Se encontrado na blacklist:
   - Log: "🚫🚫🚫 TOKEN NA BLACKLIST"
   - Log: "🚨🚨🚨 BLOQUEANDO ACESSO"
   - Retorna 401 com mensagem
6. Frontend recebe 401:
   - Limpa token do localStorage
   - Redireciona para /login
```

---

## 📝 DETALHES TÉCNICOS

### Estrutura Redis
```
blacklist:<hash_sha256>  → True (TTL: 1 hora)
user_session:<user_id>   → {session_id, token, created_at, last_activity}
user_activity:<user_id>  → timestamp ISO
```

### Por que Hash SHA256?
- Token JWT tem ~200-300 caracteres
- Redis tem limite de 250 caracteres para chaves
- Hash SHA256 sempre gera 64 caracteres (fixo)
- Impossível ter colisões (2^256 possibilidades)

### Timeout de Inatividade
- **30 minutos** sem uso → sessão expira automaticamente
- Cada requisição atualiza o timestamp de atividade
- Verificado em toda requisição

---

## 🔐 SEGURANÇA

### Isolamento Total
✅ 3 endpoints de login separados  
✅ Validação de tipo de usuário no login  
✅ Tokens JWT com `user_type`, `loja_id`, `loja_slug`  
✅ Middleware de isolamento de dados por loja  

### Sessão Única (v185)
✅ Apenas 1 sessão ativa por usuário  
✅ Logout automático ao fazer novo login  
✅ Blacklist de tokens antigos (Redis)  
✅ Validação em TODAS as requisições  
✅ Bloqueio forçado sem exceções  

---

## 📊 HISTÓRICO DE VERSÕES

| Versão | Status | Descrição |
|--------|--------|-----------|
| **v185** | ✅ **ATUAL** | Bloqueio forçado + logs detalhados |
| v184 | ❌ | Hash SHA256 mas não bloqueava |
| v183 | ❌ | Token completo (chave muito longa) |
| v182 | ✅ | SessionAwareJWTAuthentication |
| v181 | ✅ | Blacklist com Redis direto |
| v179-180 | ❌ | JWT Blacklist (não funcionou) |
| v177-178 | ✅ | Redis configurado (Heroku) |
| v174-176 | ✅ | SessionManager + Middleware |

---

## 🚀 DEPLOY

### Backend (v185) ✅
```bash
git push heroku master
```

### Frontend (v173)
```bash
cd frontend
vercel --prod --yes
```

---

## 🐛 SE NÃO FUNCIONAR

### 1. Verificar Token no Browser
- Abrir DevTools (F12)
- Aba Network
- Fazer uma requisição
- Ver Headers → Authorization: Bearer <token>
- Token deve estar presente

### 2. Verificar Resposta do Servidor
- Aba Network → Clicar na requisição
- Ver Response
- Deve retornar 401 com:
  ```json
  {
    "error": "Sessão inválida",
    "code": "BLACKLISTED",
    "message": "Token foi invalidado por nova sessão",
    "action": "FORCE_LOGOUT"
  }
  ```

### 3. Verificar Logs do Heroku
```bash
heroku logs --tail --app lwksistemas | grep "🚨🚨🚨"
```

Procurar por:
- `🚨🚨🚨 BLOQUEANDO ACESSO`
- `🚫🚫🚫 TOKEN NA BLACKLIST`
- `🚨 SESSÃO ANTERIOR DETECTADA`

### 4. Verificar Frontend
- Frontend deve ter código para tratar 401
- Deve limpar token do localStorage
- Deve redirecionar para /login

---

## 📞 INFORMAÇÕES

**URLs**:
- Frontend: https://lwksistemas.com.br
- Backend: https://lwksistemas-38ad47519238.herokuapp.com
- Logs: https://dashboard.heroku.com/apps/lwksistemas/logs

**Usuário de Teste**:
- Username: `luiz`
- Senha: `147Luiz@`
- Tipo: Super Admin

**Redis**:
- Heroku Redis Mini (gratuito)
- ~$0.004/hora
- Tempo de resposta: ~1ms

---

## ✅ CHECKLIST DE TESTE

- [ ] Fazer logout em todos os dispositivos
- [ ] Login no computador
- [ ] Navegar no sistema (computador)
- [ ] Login no celular
- [ ] Tentar usar computador → DEVE BLOQUEAR
- [ ] Verificar mensagem de erro
- [ ] Verificar redirecionamento para login
- [ ] Confirmar celular funcionando
- [ ] Ver logs do Heroku

---

## 🎯 RESULTADO ESPERADO

✅ Usuário NÃO pode usar 2 dispositivos ao mesmo tempo  
✅ Ao fazer login em novo dispositivo, o antigo é desconectado  
✅ Mensagem clara: "Você foi desconectado porque iniciou uma nova sessão em outro dispositivo"  
✅ Redirecionamento automático para login  
✅ Logs detalhados para debug  

---

**Status**: 🔄 AGUARDANDO TESTE DO USUÁRIO  
**Próximo Passo**: Testar cenário completo e reportar resultado
