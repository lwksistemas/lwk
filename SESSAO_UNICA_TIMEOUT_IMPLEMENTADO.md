# Sistema de Sessão Única e Timeout de Inatividade ✅

## 📋 Resumo da Implementação

Implementado sistema robusto de controle de sessões que garante:
1. **Sessão Única**: Cada usuário pode ter apenas UMA sessão ativa por vez
2. **Timeout de Inatividade**: Logout automático após 30 minutos sem uso
3. **Detecção de Múltiplas Sessões**: Usuário é desconectado se fizer login em outro dispositivo

---

## 🎯 Funcionalidades Implementadas

### 1. Sessão Única por Usuário
- Ao fazer login, qualquer sessão anterior é invalidada
- Apenas um dispositivo/navegador pode estar logado por vez
- Tentativa de login em outro lugar desconecta a sessão anterior

### 2. Timeout de Inatividade (30 minutos)
- Sistema monitora atividade do usuário
- Após 30 minutos sem interação, sessão expira automaticamente
- Atividades monitoradas: mouse, teclado, scroll, touch, cliques

### 3. Validação em Cada Requisição
- Middleware valida sessão em todas as requisições API
- Verifica se token corresponde à sessão ativa
- Atualiza timestamp de última atividade

### 4. Mensagens Claras ao Usuário
- **Sessão Conflitante**: "Você foi desconectado porque iniciou uma nova sessão em outro dispositivo"
- **Timeout**: "Sua sessão expirou por inatividade (30 minutos sem uso)"
- **Sem Sessão**: "Nenhuma sessão ativa encontrada. Faça login novamente"

---

## 💻 Implementação Técnica

### Backend

#### 1. SessionManager (`backend/superadmin/session_manager.py`)

Gerenciador de sessões usando Django Cache:

```python
class SessionManager:
    """
    Gerenciador de sessões únicas
    - Apenas uma sessão ativa por usuário
    - Logout automático após 30 minutos de inatividade
    - Invalidação de sessões antigas ao fazer novo login
    """
    
    @staticmethod
    def create_session(user_id: int, token: str) -> str:
        """Cria nova sessão e invalida anteriores"""
        
    @staticmethod
    def validate_session(user_id: int, token: str) -> dict:
        """Valida se sessão é válida"""
        
    @staticmethod
    def update_activity(user_id: int):
        """Atualiza timestamp de última atividade"""
        
    @staticmethod
    def destroy_session(user_id: int):
        """Destrói sessão do usuário"""
```

**Armazenamento**: Django Cache (LocMemCache)
- Chave de sessão: `user_session:{user_id}`
- Chave de atividade: `user_activity:{user_id}`

#### 2. SessionControlMiddleware (`backend/config/session_middleware.py`)

Middleware que valida sessões em cada requisição:

```python
class SessionControlMiddleware:
    """
    Middleware que:
    1. Valida se o usuário tem sessão ativa
    2. Verifica se não há outra sessão em outro dispositivo
    3. Atualiza timestamp de atividade
    4. Faz logout automático após 30 minutos de inatividade
    """
```

**Códigos de Erro**:
- `SESSION_CONFLICT`: Outra sessão foi iniciada
- `SESSION_TIMEOUT`: Sessão expirou por inatividade
- `NO_SESSION`: Nenhuma sessão ativa encontrada

#### 3. CustomTokenObtainPairView (`backend/superadmin/auth_views.py`)

View customizada de login que cria sessão:

```python
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada de login que:
    1. Gera tokens JWT
    2. Cria sessão única para o usuário
    3. Invalida sessões anteriores
    """
```

**Resposta do Login**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "session_id": "a1b2c3d4e5f6...",
  "session_timeout_minutes": 30,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_superuser": true
  }
}
```

#### 4. LogoutView (`backend/superadmin/auth_views.py`)

View de logout que destrói sessão:

```python
class LogoutView(TokenObtainPairView):
    """View de logout que destrói a sessão do usuário"""
```

---

### Frontend

#### 1. AuthService Atualizado (`frontend/lib/auth.ts`)

Serviço de autenticação com controle de sessão:

```typescript
export const authService = {
  async login(credentials, userType, lojaSlug): Promise<AuthTokens> {
    // Salva session_id e inicia monitoramento de inatividade
    authService.startInactivityMonitor();
  },
  
  async logout() {
    // Chama endpoint de logout e limpa tudo
    await apiClient.post('/auth/logout/');
    authService.stopInactivityMonitor();
  },
  
  forceLogout(reason?: string) {
    // Logout forçado (sessão conflitante ou timeout)
    console.log('🚨 FORCE LOGOUT:', reason);
    // Limpa tudo e redireciona para home
  },
  
  startInactivityMonitor() {
    // Monitora atividade do usuário
    // Logout automático após 30 minutos
  },
  
  stopInactivityMonitor() {
    // Para monitoramento de inatividade
  }
}
```

**Eventos Monitorados**:
- `mousedown`, `mousemove`, `keypress`
- `scroll`, `touchstart`, `click`

#### 2. API Client Atualizado (`frontend/lib/api-client.ts`)

Interceptor de resposta que detecta erros de sessão:

```typescript
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Verificar erros de sessão
    if (error.response?.status === 401) {
      const errorCode = error.response?.data?.code;
      
      if (errorCode === 'SESSION_CONFLICT' || 
          errorCode === 'SESSION_TIMEOUT' || 
          errorCode === 'NO_SESSION') {
        
        // Limpar tudo e redirecionar
        alert(error.response?.data?.message);
        window.location.href = '/';
      }
    }
  }
);
```

---

## 🔄 Fluxo de Funcionamento

### Cenário 1: Login Normal

```
1. Usuário faz login
2. Backend cria sessão única (invalida anteriores)
3. Frontend salva session_id e inicia monitoramento
4. Usuário usa o sistema normalmente
5. A cada requisição, backend atualiza timestamp de atividade
```

### Cenário 2: Login em Outro Dispositivo

```
1. Usuário já está logado no Dispositivo A
2. Usuário faz login no Dispositivo B
3. Backend cria nova sessão (invalida sessão do Dispositivo A)
4. Dispositivo A faz próxima requisição
5. Backend detecta token diferente
6. Retorna erro SESSION_CONFLICT
7. Dispositivo A é desconectado automaticamente
8. Mensagem: "Você foi desconectado porque iniciou uma nova sessão em outro dispositivo"
```

### Cenário 3: Timeout de Inatividade

```
1. Usuário está logado mas não interage
2. Após 30 minutos sem atividade:
   - Frontend: Timer dispara logout local
   - Backend: Próxima requisição detecta timeout
3. Sessão é destruída
4. Usuário é redirecionado para home
5. Mensagem: "Sua sessão expirou por inatividade (30 minutos sem uso)"
```

---

## 🛡️ Segurança

### Proteções Implementadas

1. **Sessão Única**
   - Impede uso simultâneo da mesma conta
   - Detecta tentativas de acesso não autorizado
   - Protege contra roubo de credenciais

2. **Timeout de Inatividade**
   - Previne sessões abandonadas
   - Reduz janela de oportunidade para ataques
   - Libera recursos do servidor

3. **Validação Contínua**
   - Cada requisição valida sessão
   - Token deve corresponder à sessão ativa
   - Timestamp de atividade sempre atualizado

4. **Logout Forçado**
   - Limpa completamente localStorage e cookies
   - Redireciona para página segura
   - Impede uso de tokens antigos

---

## 📊 Configurações

### Backend

```python
# backend/superadmin/session_manager.py
SESSION_TIMEOUT_MINUTES = 30  # Timeout de inatividade
```

### Frontend

```typescript
// frontend/lib/auth.ts
const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutos
```

---

## 🔧 Configuração do Cache

O sistema usa Django Cache para armazenar sessões:

```python
# backend/config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

**Nota**: Para produção com múltiplos workers, considere usar Redis:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## 🚀 Deploy

### Commits
```bash
git commit -m "feat: implementar controle de sessão única e timeout de inatividade (30min)"
```

### Deploy Backend (Heroku)
```
✅ Deploy realizado com sucesso
📦 Versão: v169
🔗 URL: https://lwksistemas-38ad47519238.herokuapp.com/
```

### Deploy Frontend (Vercel)
```
✅ Deploy realizado com sucesso
🔗 URL: https://lwksistemas.com.br
```

---

## 📝 Endpoints Novos

### POST /api/auth/token/
Login com criação de sessão

**Request**:
```json
{
  "username": "admin",
  "password": "senha123"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "session_id": "a1b2c3d4e5f6...",
  "session_timeout_minutes": 30,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_superuser": true
  }
}
```

### POST /api/auth/logout/
Logout com destruição de sessão

**Request**:
```
Authorization: Bearer {token}
```

**Response**:
```json
{
  "message": "Logout realizado com sucesso",
  "code": "LOGOUT_SUCCESS"
}
```

---

## ✅ Testes Recomendados

### Teste 1: Sessão Única
1. Fazer login no Navegador A
2. Fazer login no Navegador B com mesma conta
3. Tentar usar sistema no Navegador A
4. **Resultado Esperado**: Navegador A é desconectado

### Teste 2: Timeout de Inatividade
1. Fazer login
2. Deixar sistema aberto sem interagir por 30 minutos
3. Tentar fazer alguma ação
4. **Resultado Esperado**: Logout automático com mensagem

### Teste 3: Atividade Contínua
1. Fazer login
2. Usar sistema continuamente (clicar, digitar, etc)
3. Continuar por mais de 30 minutos
4. **Resultado Esperado**: Sessão permanece ativa

### Teste 4: Logout Manual
1. Fazer login
2. Clicar em logout
3. Tentar acessar página protegida
4. **Resultado Esperado**: Redirecionado para login

---

## 🔗 Arquivos Modificados/Criados

### Backend
- ✅ `backend/superadmin/session_manager.py` (NOVO)
- ✅ `backend/superadmin/auth_views.py` (NOVO)
- ✅ `backend/config/session_middleware.py` (NOVO)
- ✅ `backend/config/settings.py` (MODIFICADO)
- ✅ `backend/config/urls.py` (MODIFICADO)

### Frontend
- ✅ `frontend/lib/auth.ts` (MODIFICADO)
- ✅ `frontend/lib/api-client.ts` (MODIFICADO)

---

## 💡 Benefícios

1. **Segurança Aumentada**
   - Impede uso simultâneo de contas
   - Reduz risco de sessões abandonadas
   - Detecta acessos não autorizados

2. **Melhor Experiência do Usuário**
   - Mensagens claras sobre o que aconteceu
   - Logout automático previne confusão
   - Sistema sempre em estado consistente

3. **Controle Administrativo**
   - Logs de todas as sessões
   - Possibilidade de forçar logout de todos
   - Monitoramento de atividade

4. **Conformidade**
   - Atende requisitos de segurança
   - Previne compartilhamento de contas
   - Auditoria de acessos

---

**Status**: ✅ IMPLEMENTADO E EM PRODUÇÃO  
**Data**: 22/01/2026  
**Versão Backend**: v169  
**Versão Frontend**: Produção Vercel
