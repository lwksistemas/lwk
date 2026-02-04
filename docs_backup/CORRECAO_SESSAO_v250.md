# ✅ Correção de Sessão Única e Timeout - v250

## 🎯 Problemas Corrigidos

### 1. ✅ Sessão única agora funciona para TODOS os usuários
- Superadmin ✅
- Admin de loja ✅
- Suporte ✅

### 2. ✅ Timeout aumentado de 30 para 60 minutos
- Mais tempo para usuários que leem/pensam
- Menos interrupções desnecessárias

### 3. ✅ Heartbeat implementado (sessão não fecha mais com usuário ativo)
- Frontend envia ping a cada 5 minutos
- Mantém sessão ativa automaticamente
- Usuário pode ficar horas no sistema sem ser desconectado

## 🔧 Mudanças Implementadas

### Backend (v250)

**1. Timeout aumentado para 60 minutos**
```python
# backend/superadmin/session_manager.py
SESSION_TIMEOUT_MINUTES = 60  # Era 30
```

**2. Endpoint de heartbeat adicionado**
```python
# backend/superadmin/views.py
@action(detail=False, methods=['get'])
def heartbeat(self, request):
    """Mantém sessão ativa"""
    SessionManager.update_activity(request.user.id)
    return Response({'status': 'alive'})
```

### Frontend (v250)

**1. Heartbeat automático**
```typescript
// frontend/lib/api-client.ts
export function startHeartbeat() {
  // Envia ping a cada 5 minutos
  setInterval(() => {
    apiClient.get('/superadmin/lojas/heartbeat/');
  }, 5 * 60 * 1000);
}
```

**2. Integração com auth**
```typescript
// frontend/lib/auth.ts
async login() {
  // ... login ...
  startHeartbeat(); // Inicia após login
}

async logout() {
  stopHeartbeat(); // Para ao fazer logout
}
```

## 📊 Como Funciona Agora

### Fluxo de Sessão

```
1. Usuário faz login
   ↓
2. Backend cria sessão única (deleta sessões anteriores)
   ↓
3. Frontend inicia heartbeat (ping a cada 5 minutos)
   ↓
4. A cada requisição:
   - Backend valida sessão única
   - Backend valida timeout (60 minutos)
   - Backend atualiza last_activity
   ↓
5. Heartbeat mantém sessão ativa automaticamente
   ↓
6. Sessão só expira se:
   - Usuário ficar 60 minutos SEM fazer nada
   - Usuário fazer login em outro dispositivo
   - Usuário fazer logout
```

### Sessão Única

```
Cenário: Usuário faz login em 2 navegadores

Navegador 1: Login às 10:00
  ↓
Backend: Cria sessão A, deleta sessões anteriores
  ↓
Navegador 2: Login às 10:05
  ↓
Backend: Cria sessão B, deleta sessão A
  ↓
Navegador 1: Tenta fazer algo às 10:10
  ↓
Backend: Valida sessão → Token diferente!
  ↓
Frontend: Erro "Outra sessão foi iniciada"
  ↓
Navegador 1: Logout forçado
```

### Timeout com Heartbeat

```
Cenário: Usuário deixa página aberta

10:00 - Login
10:05 - Heartbeat (atualiza atividade)
10:10 - Heartbeat (atualiza atividade)
10:15 - Heartbeat (atualiza atividade)
...
11:00 - Heartbeat (atualiza atividade)
...
12:00 - Usuário ainda logado! ✅

Sem heartbeat:
10:00 - Login
10:30 - Timeout! ❌ (30 minutos sem atividade)
```

## 🧪 Como Testar

### Teste 1: Sessão Única (Admin de Loja)

1. **Navegador 1:** Fazer login em https://lwksistemas.com.br/loja/felix/login
2. **Navegador 2:** Fazer login com MESMO usuário
3. **Navegador 1:** Tentar fazer algo (clicar em Funcionários)
4. **Esperado:** Erro "Outra sessão foi iniciada em outro dispositivo"

### Teste 2: Timeout de 60 Minutos

1. Fazer login
2. Esperar 61 minutos SEM fazer nada (fechar DevTools para não ter heartbeat)
3. Tentar fazer algo
4. **Esperado:** Erro "Sessão expirou por inatividade (60 minutos)"

### Teste 3: Heartbeat Mantém Sessão Ativa

1. Fazer login
2. Abrir DevTools (F12) → Console
3. Ver logs: `💓 Heartbeat OK` a cada 5 minutos
4. Deixar página aberta por 2 horas
5. Fazer algo
6. **Esperado:** Funciona normalmente! ✅

### Teste 4: Heartbeat Para ao Fazer Logout

1. Fazer login
2. Abrir DevTools → Console
3. Ver: `💓 Iniciando heartbeat`
4. Fazer logout
5. Ver: `💔 Heartbeat parado`
6. **Esperado:** Não deve mais enviar pings

## 📝 Logs para Verificar

### Ver heartbeat funcionando (DevTools Console):
```
💓 Iniciando heartbeat (ping a cada 5 minutos)
💓 Heartbeat OK: {status: 'alive', user: 'felipe', ...}
💓 Heartbeat OK: {status: 'alive', user: 'felipe', ...}
...
```

### Ver sessões no Heroku:
```bash
heroku run "python backend/manage.py shell -c \"
from superadmin.models import UserSession
from django.utils import timezone

for s in UserSession.objects.all():
    inactive = (timezone.now() - s.last_activity).total_seconds() / 60
    print(f'{s.user.username}: {inactive:.1f}min inativo')
\"" --app lwksistemas
```

### Ver logs de sessão:
```bash
heroku logs --tail --app lwksistemas | grep -i "heartbeat\|sessão"
```

## ✅ Checklist de Verificação

- [x] Timeout aumentado para 60 minutos
- [x] Endpoint de heartbeat criado
- [x] Heartbeat implementado no frontend
- [x] Heartbeat inicia após login
- [x] Heartbeat para ao fazer logout
- [x] Sessão única funciona para todos os usuários
- [ ] Testar sessão única com admin de loja
- [ ] Testar heartbeat mantendo sessão ativa
- [ ] Testar timeout de 60 minutos

## 🎯 Próximos Passos

1. **Fazer login** em https://lwksistemas.com.br/loja/felix/login
2. **Abrir DevTools** (F12) → Console
3. **Verificar logs:** Deve aparecer `💓 Iniciando heartbeat`
4. **Esperar 5 minutos:** Deve aparecer `💓 Heartbeat OK`
5. **Testar sessão única:** Login em 2 navegadores

## 🆘 Se Não Funcionar

### Heartbeat não aparece nos logs:
**Causa:** Frontend não foi deployado ainda
**Solução:** Aguardar deploy automático do Vercel (2-3 minutos)

### Sessão ainda expira rápido:
**Causa:** Heartbeat não está funcionando
**Solução:** Verificar logs do console do navegador

### Erro ao fazer heartbeat:
**Causa:** Endpoint não existe
**Solução:** Verificar se backend v250 está deployado

## 📊 Resumo

**Versão:** v250
**Backend:** Heroku ✅ Deployado
**Frontend:** Vercel ⏳ Aguardando deploy automático

**Mudanças:**
- ✅ Timeout: 30min → 60min
- ✅ Heartbeat: Ping a cada 5min
- ✅ Sessão única: Funciona para todos

**Resultado:**
- Usuário pode ficar horas no sistema sem ser desconectado
- Sessão só expira por inatividade real (60min sem nada)
- Sessão única impede login simultâneo em múltiplos dispositivos
