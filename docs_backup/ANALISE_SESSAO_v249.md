# 🔍 Análise de Problemas de Sessão - v249

## ❌ Problemas Identificados

### 1. Sessão única não funciona para admin de loja
**Status:** ✅ FUNCIONA mas pode ter bug
**Causa:** O código está correto, mas pode haver problema no frontend

### 2. Timeout de 30min não funciona para admin de loja  
**Status:** ✅ FUNCIONA mas pode ter bug
**Causa:** O código está correto, mas pode haver problema no frontend

### 3. Timeout fecha sessão mesmo com usuário ativo
**Status:** ❌ BUG CONFIRMADO
**Causa:** `update_activity()` só é chamado em requisições autenticadas, mas o frontend pode não estar fazendo requisições frequentes

## 🔍 Código Atual

### SessionManager (backend/superadmin/session_manager.py)
```python
# Cria sessão única (deleta sessões anteriores)
SessionManager.create_session(user_id, token)

# Valida sessão (verifica token e timeout)
SessionManager.validate_session(user_id, token)

# Atualiza atividade (reseta timeout)
SessionManager.update_activity(user_id)
```

### SessionAwareJWTAuthentication (backend/superadmin/authentication.py)
```python
# Valida TODAS as requisições (exceto /api/auth/)
def authenticate(self, request):
    # 1. Valida JWT
    # 2. Valida sessão única
    # 3. Valida timeout
    # 4. Atualiza atividade ← AQUI
```

### SecureLoginView (backend/superadmin/auth_views_secure.py)
```python
# Cria sessão para TODOS os usuários
session_id = SessionManager.create_session(user.id, access)
```

## 🎯 Problemas Reais

### Problema 1: Frontend não está atualizando atividade
**Causa:** Se o usuário fica na mesma página sem fazer requisições, a atividade não é atualizada.

**Solução:** Adicionar heartbeat no frontend (ping a cada 5 minutos)

### Problema 2: Timeout muito agressivo
**Causa:** 30 minutos pode ser pouco se o usuário está lendo/pensando

**Solução:** Aumentar para 60 minutos ou adicionar heartbeat

### Problema 3: Sessão única pode não estar funcionando no frontend
**Causa:** Frontend pode estar guardando token antigo no localStorage

**Solução:** Limpar localStorage ao receber erro de sessão

## 🔧 Soluções

### Solução 1: Adicionar Heartbeat no Frontend (RECOMENDADO)

Adicionar em `frontend/lib/api-client.ts`:

```typescript
// Heartbeat para manter sessão ativa
let heartbeatInterval: NodeJS.Timeout | null = null;

export function startHeartbeat() {
  if (heartbeatInterval) return;
  
  heartbeatInterval = setInterval(async () => {
    try {
      // Ping simples para atualizar atividade
      await apiClient.get('/auth/heartbeat/');
      console.log('💓 Heartbeat enviado');
    } catch (error) {
      console.error('❌ Heartbeat falhou:', error);
      // Se falhar, pode ser que a sessão expirou
      if (error.response?.status === 401) {
        stopHeartbeat();
        localStorage.clear();
        window.location.href = '/';
      }
    }
  }, 5 * 60 * 1000); // A cada 5 minutos
}

export function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
}
```

### Solução 2: Aumentar Timeout para 60 minutos

Alterar em `backend/superadmin/session_manager.py`:

```python
SESSION_TIMEOUT_MINUTES = 60  # Era 30
```

### Solução 3: Adicionar Endpoint de Heartbeat

Criar em `backend/superadmin/views.py`:

```python
@action(detail=False, methods=['get'])
def heartbeat(self, request):
    """Endpoint para manter sessão ativa"""
    return Response({
        'status': 'alive',
        'user': request.user.username,
        'timestamp': timezone.now().isoformat()
    })
```

## 🧪 Como Testar

### Teste 1: Sessão Única
1. Fazer login no navegador 1
2. Fazer login no navegador 2 com mesmo usuário
3. Tentar usar navegador 1
4. **Esperado:** Erro "Outra sessão foi iniciada"

### Teste 2: Timeout
1. Fazer login
2. Esperar 31 minutos SEM fazer nada
3. Tentar fazer uma ação
4. **Esperado:** Erro "Sessão expirou por inatividade"

### Teste 3: Heartbeat (após implementar)
1. Fazer login
2. Deixar página aberta por 1 hora
3. Fazer uma ação
4. **Esperado:** Funciona normalmente (heartbeat manteve sessão ativa)

## 📊 Logs para Debug

### Ver sessões ativas:
```bash
heroku run "python backend/manage.py shell -c \"
from superadmin.models import UserSession
from django.utils import timezone

sessions = UserSession.objects.all()
print(f'Total de sessões: {sessions.count()}')

for s in sessions:
    now = timezone.now()
    inactive = (now - s.last_activity).total_seconds() / 60
    print(f'  {s.user.username}: {inactive:.1f}min inativo')
\"" --app lwksistemas
```

### Ver se sessão está sendo validada:
```bash
heroku logs --tail --app lwksistemas | grep -i "sessão\|session"
```

## 🎯 Ação Imediata

Me diga:
1. **Você consegue fazer login em 2 navegadores com mesmo usuário de loja?**
2. **A sessão fecha após 30 minutos mesmo usando o sistema?**
3. **Quer que eu implemente o heartbeat?**
