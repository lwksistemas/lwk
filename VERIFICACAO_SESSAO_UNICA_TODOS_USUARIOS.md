# ✅ Verificação: Sessão Única para TODOS os Usuários

## 🎯 Pergunta
**Todos os usuários do sistema não podem ter 2 sessões ativas?**
- Usuários do suporte
- Usuários das lojas (proprietários)
- Funcionários das lojas

## ✅ RESPOSTA: SIM, TODOS ESTÃO PROTEGIDOS!

## 🔐 Como Funciona

### 1. Authenticator Global (SessionAwareJWTAuthentication)

**Arquivo:** `backend/superadmin/authentication.py`

```python
class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    Authenticator JWT que verifica sessão única usando PostgreSQL
    Garante que cada usuário tenha apenas uma sessão ativa por vez
    """
```

**Configuração Global:**
```python
# backend/config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'superadmin.authentication.SessionAwareJWTAuthentication',  # 🔐 GLOBAL
    ],
}
```

**Isso significa:**
- ✅ TODAS as requisições autenticadas passam por este authenticator
- ✅ TODOS os usuários têm sessão única validada
- ✅ Não importa o tipo de usuário (superadmin, suporte, loja, funcionário)

### 2. Login Cria Sessão para TODOS

**Arquivo:** `backend/superadmin/auth_views_secure.py`

```python
class SecureLoginView(APIView):
    def post(self, request, user_type=None):
        # ... autenticação ...
        
        # Criar sessão única (PARA TODOS)
        session_id = SessionManager.create_session(user.id, access)
```

**Endpoints que criam sessão:**
1. ✅ `/api/auth/superadmin/login/` - Superadmin
2. ✅ `/api/auth/suporte/login/` - Suporte
3. ✅ `/api/auth/loja/login/` - Proprietários de loja

### 3. Validação em TODA Requisição

**Fluxo:**
```
1. Usuário faz requisição com token JWT
2. SessionAwareJWTAuthentication intercepta
3. Valida JWT (padrão)
4. Valida sessão única no banco de dados
5. Se sessão inválida → 401 UNAUTHORIZED
6. Se sessão válida → Continua
```

**Código:**
```python
def authenticate(self, request):
    # Autenticação JWT padrão
    result = super().authenticate(request)
    
    # Validar sessão usando banco de dados
    validation = SessionManager.validate_session(user.id, token_str)
    
    if not validation['valid']:
        raise AuthenticationFailed({
            'detail': validation['message'],
            'code': validation['reason']
        })
```

## 👥 Tipos de Usuários Protegidos

### 1. ✅ Superadmin
- **Login:** `/api/auth/superadmin/login/`
- **Cria sessão:** ✅ Sim
- **Valida sessão:** ✅ Sim (em toda requisição)
- **Sessão única:** ✅ Garantida

### 2. ✅ Suporte
- **Login:** `/api/auth/suporte/login/`
- **Cria sessão:** ✅ Sim
- **Valida sessão:** ✅ Sim (em toda requisição)
- **Sessão única:** ✅ Garantida

### 3. ✅ Proprietários de Loja
- **Login:** `/api/auth/loja/login/`
- **Cria sessão:** ✅ Sim
- **Valida sessão:** ✅ Sim (em toda requisição)
- **Sessão única:** ✅ Garantida

### 4. ✅ Funcionários de Loja
- **Login:** `/api/auth/loja/login/` (mesmo endpoint)
- **Cria sessão:** ✅ Sim
- **Valida sessão:** ✅ Sim (em toda requisição)
- **Sessão única:** ✅ Garantida

**Nota:** Funcionários usam o mesmo sistema de autenticação que proprietários, pois são usuários vinculados à loja.

## 🔍 Verificação Prática

### Cenário 1: Superadmin
```
1. Superadmin faz login no computador → Sessão A criada
2. Superadmin tenta login no celular → Sessão A destruída, Sessão B criada
3. Superadmin tenta usar computador → 401 UNAUTHORIZED (sessão inválida)
```

### Cenário 2: Suporte
```
1. Suporte faz login no computador → Sessão A criada
2. Suporte tenta login no tablet → Sessão A destruída, Sessão B criada
3. Suporte tenta usar computador → 401 UNAUTHORIZED (sessão inválida)
```

### Cenário 3: Proprietário de Loja
```
1. Proprietário faz login no computador → Sessão A criada
2. Proprietário tenta login no celular → Sessão A destruída, Sessão B criada
3. Proprietário tenta usar computador → 401 UNAUTHORIZED (sessão inválida)
```

### Cenário 4: Funcionário de Loja
```
1. Funcionário faz login no tablet → Sessão A criada
2. Funcionário tenta login em outro tablet → Sessão A destruída, Sessão B criada
3. Funcionário tenta usar primeiro tablet → 401 UNAUTHORIZED (sessão inválida)
```

## 📊 Tabela de Sessões (Banco de Dados)

**Modelo:** `UserSession`

```python
class UserSession(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # ← OneToOne = Sessão Única
    session_id = models.CharField(max_length=255, unique=True)
    token_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

**Importante:**
- `OneToOneField` = Cada usuário pode ter APENAS 1 sessão
- Quando novo login acontece, sessão antiga é DESTRUÍDA
- Funciona para TODOS os tipos de usuário

## 🛡️ Códigos de Erro

Quando sessão é inválida, o sistema retorna:

```json
{
  "detail": "Outra sessão foi iniciada em outro dispositivo",
  "code": "DIFFERENT_SESSION",
  "message": "Outra sessão foi iniciada em outro dispositivo"
}
```

**Outros códigos:**
- `DIFFERENT_SESSION` - Login em outro dispositivo
- `SESSION_CONFLICT` - Conflito de sessão
- `SESSION_TIMEOUT` - Sessão expirou por inatividade (30 min)
- `NO_SESSION` - Nenhuma sessão encontrada

## 🎯 Conclusão

### ✅ TODOS os usuários estão protegidos:

1. **Superadmin** ✅
2. **Suporte** ✅
3. **Proprietários de Loja** ✅
4. **Funcionários de Loja** ✅

### Como é garantido:

1. **Authenticator Global:** Todas as requisições passam por `SessionAwareJWTAuthentication`
2. **Sessão no Login:** Todos os endpoints de login criam sessão via `SessionManager.create_session()`
3. **Validação Contínua:** Toda requisição valida sessão no banco de dados
4. **OneToOne Constraint:** Banco de dados garante apenas 1 sessão por usuário

### Não há exceções:

- ❌ Não há endpoint sem validação de sessão
- ❌ Não há tipo de usuário sem sessão única
- ❌ Não há forma de ter 2 sessões ativas

## 🧪 Como Testar

### Teste Manual:

1. Faça login como qualquer tipo de usuário (superadmin, suporte, loja)
2. Copie o token de acesso
3. Faça login novamente no mesmo usuário
4. Tente usar o primeiro token
5. Resultado esperado: **401 UNAUTHORIZED**

### Teste Automático:

```bash
# Login 1
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha123"}'

# Salvar token1

# Login 2 (mesmo usuário)
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/superadmin/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha123"}'

# Salvar token2

# Tentar usar token1 (deve falhar)
curl -X GET https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/ \
  -H "Authorization: Bearer TOKEN1"

# Resultado: 401 UNAUTHORIZED
```

## 📝 Notas Importantes

1. **Timeout de Inatividade:** 30 minutos sem atividade = logout automático
2. **Frontend:** Detecta erro de sessão e faz logout automático
3. **Mensagem ao Usuário:** "Outra sessão foi iniciada em outro dispositivo"
4. **Segurança:** Impossível ter 2 sessões ativas do mesmo usuário

---

**Status:** ✅ TODOS os usuários têm sessão única garantida
**Versão:** v227 (Backend) + Frontend otimizado
**Data:** 25/01/2026
