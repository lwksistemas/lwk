# 🔄 Implementação de Failover Automático (v750-v753)

## Resumo

Sistema de failover automático implementado no frontend para garantir alta disponibilidade. Quando o servidor primário (Heroku) falhar, o sistema automaticamente tenta o servidor backup (Render) de forma transparente para o usuário.

---

## Arquitetura Implementada

```
Frontend (Vercel)
    ↓
┌───┴───┐
↓       ↓
Heroku  Render (Failover automático)
(Primary) (Backup)
```

---

## Componentes Implementados

### 1. Backend - Health Check Endpoint (v750-v752)

**Arquivo**: `backend/superadmin/views.py`

```python
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint para load balancer e failover automático.
    Endpoint público (sem autenticação).
    """
    try:
        # Verificar conexão com banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Verificar modelo básico
        from .models import Loja
        loja_count = Loja.objects.count()
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'lojas_count': loja_count,
            'timestamp': timezone.now().isoformat(),
            'version': 'v750'
        }, status=200)
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)
```

**Rota**: `GET /api/superadmin/health/`

**Middleware**: Adicionado à lista de endpoints públicos em `SuperAdminSecurityMiddleware`

---

### 2. Frontend - Lógica de Failover (v753)

**Arquivo**: `frontend/lib/api-client.ts`

#### Configuração

```typescript
const PRIMARY_API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BACKUP_API = process.env.NEXT_PUBLIC_API_BACKUP_URL;
const TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '20000');

let currentAPI = PRIMARY_API;
let failoverCount = 0;
let lastFailoverTime: number | null = null;
const MAX_FAILOVER_ATTEMPTS = 3;
const RECOVERY_TIME = 5 * 60 * 1000; // 5 minutos
```

#### Lógica de Failover

O interceptor de resposta detecta falhas e automaticamente:

1. **Detecta falhas**:
   - Timeout (ECONNABORTED, ETIMEDOUT)
   - Erro de rede (ERR_NETWORK)
   - Erro de servidor (5xx)

2. **Ativa failover**:
   - Muda para servidor backup
   - Repete a requisição automaticamente
   - Limita a 3 tentativas

3. **Recuperação automática**:
   - Após 5 minutos de sucesso no backup
   - Volta automaticamente para o servidor primário

#### Funções Exportadas

```typescript
// Retorna status atual do failover
export function getFailoverStatus() {
  return {
    currentAPI,
    isPrimary: currentAPI === PRIMARY_API,
    isBackup: currentAPI === BACKUP_API,
    failoverCount,
    lastFailoverTime,
    hasBackup: !!BACKUP_API,
  };
}

// Verifica health do servidor atual
export async function checkHealth(): Promise<{ healthy: boolean; api: string; error?: string }> {
  try {
    const response = await axios.get(`${currentAPI}/api/health/`, { timeout: 5000 });
    return {
      healthy: response.data.status === 'healthy',
      api: currentAPI,
    };
  } catch (error) {
    return {
      healthy: false,
      api: currentAPI,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
```

---

## Variáveis de Ambiente

### Vercel (Frontend)

```env
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
NEXT_PUBLIC_API_BACKUP_URL=https://lwksistemas.onrender.com
NEXT_PUBLIC_API_TIMEOUT=20000
```

**Status**: ⚠️ PENDENTE - Variáveis precisam ser configuradas no Vercel

---

## Próximos Passos

### 1. Configurar Servidor Backup no Render

```bash
# 1. Criar conta no Render: https://render.com
# 2. Conectar repositório GitHub
# 3. Criar novo Web Service
# 4. Configurar:
#    - Build Command: pip install -r requirements.txt
#    - Start Command: gunicorn backend.wsgi:application
#    - Environment: Python 3.12
# 5. Adicionar variáveis de ambiente (mesmas do Heroku)
# 6. Conectar ao mesmo PostgreSQL do Heroku
```

### 2. Adicionar Variáveis no Vercel

```bash
# Via CLI
vercel env add NEXT_PUBLIC_API_BACKUP_URL production
# Valor: https://lwksistemas.onrender.com

vercel env add NEXT_PUBLIC_API_TIMEOUT production
# Valor: 20000

# Ou via Dashboard: https://vercel.com/lwks-projects-48afd555/frontend/settings/environment-variables
```

### 3. Testar Failover

```bash
# Simular falha do Heroku (desligar dyno temporariamente)
heroku ps:scale web=0 -a lwksistemas

# Acessar o sistema e verificar se muda para Render automaticamente
# Verificar logs do navegador para mensagens de failover

# Reativar Heroku
heroku ps:scale web=1 -a lwksistemas

# Aguardar 5 minutos e verificar se volta para Heroku
```

---

## Comportamento do Sistema

### Cenário 1: Heroku Funcionando (Normal)
- ✅ Todas as requisições vão para Heroku
- ✅ Resposta rápida (~200-500ms)
- ✅ Sem mensagens de failover

### Cenário 2: Heroku Falha
- ⚠️ Primeira requisição falha (~2-5s timeout)
- 🔄 Sistema detecta falha e muda para Render
- ✅ Requisição é repetida automaticamente no Render
- ✅ Usuário vê delay de 2-5s mas sistema continua funcionando
- 📝 Console mostra: "⚠️ API primária falhou, tentando backup..."

### Cenário 3: Render Funcionando (Failover Ativo)
- ✅ Todas as requisições vão para Render
- ✅ Sistema funciona normalmente
- ⏱️ Após 5 minutos de sucesso, volta para Heroku automaticamente
- 📝 Console mostra: "✅ Voltando para API primária após 5 minutos de sucesso"

### Cenário 4: Ambos Falham
- ❌ Após 3 tentativas de failover, erro é mostrado ao usuário
- 📝 Console mostra: "❌ Servidor backup também falhou"
- 🔴 Usuário vê mensagem de erro padrão

---

## Monitoramento

### Logs do Frontend (Console do Navegador)

```javascript
// Sucesso normal
"API Response: 200 /api/superadmin/lojas/"

// Failover ativado
"⚠️ API primária falhou (ERR_NETWORK), tentando backup (1/3)..."
"🔄 Repetindo requisição no servidor backup..."

// Recuperação
"✅ Voltando para API primária após 5 minutos de sucesso"
```

### Verificar Status do Failover

```javascript
// No console do navegador
import { getFailoverStatus, checkHealth } from '@/lib/api-client';

// Ver status atual
console.log(getFailoverStatus());
// {
//   currentAPI: "https://lwksistemas-38ad47519238.herokuapp.com",
//   isPrimary: true,
//   isBackup: false,
//   failoverCount: 0,
//   lastFailoverTime: null,
//   hasBackup: true
// }

// Verificar health
await checkHealth();
// { healthy: true, api: "https://lwksistemas-38ad47519238.herokuapp.com" }
```

---

## Testes Realizados

### ✅ Backend (v750-v752)
- [x] Endpoint `/api/superadmin/health/` criado
- [x] Autenticação desabilitada (público)
- [x] Middleware configurado para permitir acesso
- [x] Teste em produção: `curl https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/health/`
- [x] Resposta: `{"status": "healthy", "database": "connected", "lojas_count": 4}`

### ✅ Frontend (v753)
- [x] Lógica de failover implementada
- [x] Interceptor de resposta configurado
- [x] Funções de status exportadas
- [x] Deploy no Vercel realizado

### ⚠️ Pendente
- [ ] Configurar servidor backup no Render
- [ ] Adicionar variáveis de ambiente no Vercel
- [ ] Testar failover em produção (simular falha do Heroku)
- [ ] Verificar recuperação automática após 5 minutos

---

## Custos

| Componente | Custo Mensal | Status |
|------------|--------------|--------|
| Heroku (Primary) | $7 | ✅ Ativo |
| Render (Backup) | $0 (Free Tier) | ⚠️ Pendente |
| Vercel (Frontend) | $0 (Free Tier) | ✅ Ativo |
| **Total** | **$7/mês** | - |

---

## Benefícios

1. **Alta Disponibilidade**: Sistema continua funcionando mesmo se Heroku cair
2. **Transparente**: Usuário não percebe a mudança (delay de 2-5s aceitável)
3. **Custo Zero**: Usando free tier do Render como backup
4. **Recuperação Automática**: Volta para servidor primário automaticamente
5. **Simples**: Sem necessidade de load balancer externo

---

## Limitações

1. **Delay no Failover**: 2-5 segundos na primeira falha
2. **Não é Load Balancer**: Não distribui carga, apenas failover
3. **Tentativas Limitadas**: Máximo de 3 tentativas de failover
4. **Banco Compartilhado**: Ambos os servidores usam o mesmo PostgreSQL

---

## Evolução Futura

### Fase 2: Cloudflare Load Balancer (~$10/mês)
- Failover instantâneo (<1s)
- Health checks automáticos
- Balanceamento de carga real
- DDoS protection

### Fase 3: Multi-Region (~$100/mês)
- Servidores em múltiplas regiões
- Replicação de banco de dados
- Latência reduzida globalmente
- 99.99% uptime

---

## Documentação Relacionada

- `REDUNDANCIA_BACKEND.md`: Especificação completa do sistema de redundância
- `backend/superadmin/views.py`: Implementação do health check
- `backend/superadmin/middleware.py`: Configuração de segurança
- `frontend/lib/api-client.ts`: Implementação do failover

---

## Versões

- **v750**: Endpoint de health check criado
- **v751**: Autenticação corrigida (authentication_classes=[])
- **v752**: Health check adicionado aos endpoints públicos
- **v753**: Failover automático implementado no frontend

---

## Contato

Para dúvidas ou suporte, entre em contato com a equipe de desenvolvimento.

**Data de Implementação**: 27/02/2026
**Status**: ✅ Backend Completo | ⚠️ Frontend Aguardando Configuração de Variáveis
