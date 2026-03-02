# 🔄 Redundância de Backend - Heroku + Render

## Arquitetura Atual
```
Frontend (Vercel)
    ↓
Backend (Heroku)
    ↓
PostgreSQL (Heroku)
```

## Arquitetura com Redundância
```
Frontend (Vercel)
    ↓
┌───┴───┐
↓       ↓
Heroku  Render (Failover automático)
↓       ↓
PostgreSQL (compartilhado ou replicado)
```

---

## Opção 1: Failover Automático no Frontend (RECOMENDADO)

### Vantagens
- ✅ Simples de implementar
- ✅ Sem custo adicional
- ✅ Failover em ~2 segundos
- ✅ Transparente para o usuário

### Desvantagens
- ⚠️ Delay de 2-5s na primeira falha
- ⚠️ Não balanceia carga (só failover)

### Implementação

#### 1. Configurar variáveis de ambiente

**Vercel (.env.production)**:
```env
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
NEXT_PUBLIC_API_BACKUP_URL=https://lwksistemas.onrender.com
NEXT_PUBLIC_API_TIMEOUT=10000
```

#### 2. Modificar `api-client.ts`

```typescript
// frontend/lib/api-client.ts
const PRIMARY_API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BACKUP_API = process.env.NEXT_PUBLIC_API_BACKUP_URL;
const TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000');

let currentAPI = PRIMARY_API;
let failoverCount = 0;
const MAX_FAILOVER_ATTEMPTS = 3;

// Interceptor de resposta com failover
apiClient.interceptors.response.use(
  (response) => {
    // Se sucesso, resetar para primary após 5 minutos
    if (currentAPI === BACKUP_API) {
      setTimeout(() => {
        currentAPI = PRIMARY_API;
        failoverCount = 0;
        console.log('✅ Voltando para API primária');
      }, 5 * 60 * 1000);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Se erro de rede e não tentou failover ainda
    if (
      BACKUP_API &&
      !originalRequest._retry &&
      (error.code === 'ECONNABORTED' || 
       error.code === 'ERR_NETWORK' ||
       error.response?.status >= 500)
    ) {
      originalRequest._retry = true;
      failoverCount++;

      if (failoverCount <= MAX_FAILOVER_ATTEMPTS) {
        console.warn(`⚠️ API primária falhou, tentando backup (${failoverCount}/${MAX_FAILOVER_ATTEMPTS})...`);
        
        // Mudar para backup
        currentAPI = BACKUP_API;
        originalRequest.baseURL = BACKUP_API + '/api';
        
        return apiClient(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);
```

#### 3. Deploy no Render

**Passos:**
1. Criar conta no Render: https://render.com
2. Conectar repositório GitHub
3. Criar novo Web Service
4. Configurar:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn backend.wsgi:application`
   - **Environment**: Python 3.12
5. Adicionar variáveis de ambiente (mesmas do Heroku)
6. Conectar ao mesmo PostgreSQL do Heroku

---

## Opção 2: Load Balancer com Cloudflare (PROFISSIONAL)

### Vantagens
- ✅ Failover instantâneo (<1s)
- ✅ Health checks automáticos
- ✅ Balanceamento de carga real
- ✅ DDoS protection incluído
- ✅ Cache global

### Desvantagens
- 💰 Custo: $5-20/mês
- ⚙️ Configuração mais complexa

### Implementação

#### 1. Configurar Cloudflare Load Balancer

```
1. Adicionar domínio ao Cloudflare
2. Criar Load Balancer:
   - Pool 1 (Primary): lwksistemas-38ad47519238.herokuapp.com
   - Pool 2 (Backup): lwksistemas.onrender.com
3. Configurar Health Checks:
   - Endpoint: /api/health/
   - Interval: 60s
   - Timeout: 5s
4. Steering Policy: "Failover"
```

#### 2. Criar endpoint de health check

```python
# backend/superadmin/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check para load balancer"""
    try:
        # Verificar conexão com banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)

# backend/superadmin/urls.py
urlpatterns = [
    path('health/', health_check, name='health-check'),
    # ... outras rotas
]
```

#### 3. Atualizar frontend

```typescript
// frontend/lib/api-client.ts
const API_URL = 'https://api.lwksistemas.com.br'; // Cloudflare Load Balancer
```

---

## Opção 3: Multi-Region com Replicação (ENTERPRISE)

### Arquitetura
```
Frontend (Vercel - Global CDN)
    ↓
Cloudflare Load Balancer
    ↓
┌───────┴───────┐
↓               ↓
Heroku (US)     Render (EU)
↓               ↓
PostgreSQL Master-Slave Replication
```

### Vantagens
- ✅ Latência reduzida globalmente
- ✅ Alta disponibilidade (99.99%)
- ✅ Disaster recovery automático

### Desvantagens
- 💰 Custo alto ($50-200/mês)
- ⚙️ Complexidade alta
- 🔧 Requer sincronização de banco

---

## Comparação de Custos

| Solução | Custo Mensal | Complexidade | Downtime |
|---------|--------------|--------------|----------|
| **Failover Frontend** | $0 | Baixa | 2-5s |
| **Cloudflare LB** | $5-20 | Média | <1s |
| **Multi-Region** | $50-200 | Alta | <100ms |

---

## Recomendação

### Para seu caso (lwksistemas):

**Fase 1 (Agora)**: Implementar Failover no Frontend
- Custo: $0
- Tempo: 1-2 horas
- Proteção: 90% dos casos

**Fase 2 (Futuro)**: Adicionar Cloudflare Load Balancer
- Quando: >100 lojas ou receita >R$10k/mês
- Custo: ~$10/mês
- Proteção: 99.9% uptime

**Fase 3 (Escala)**: Multi-Region
- Quando: >1000 lojas ou internacional
- Custo: ~$100/mês
- Proteção: 99.99% uptime

---

## Próximos Passos

### 1. Deploy no Render (Backup)
```bash
# 1. Criar conta no Render
# 2. Conectar GitHub
# 3. Criar Web Service
# 4. Configurar variáveis de ambiente
# 5. Deploy automático
```

### 2. Implementar Failover
```bash
# Adicionar variável no Vercel
vercel env add NEXT_PUBLIC_API_BACKUP_URL production
# Valor: https://lwksistemas.onrender.com

# Modificar api-client.ts (código acima)
# Deploy
vercel --prod
```

### 3. Testar Failover
```bash
# Simular falha do Heroku
# Verificar se frontend muda para Render automaticamente
# Monitorar logs
```

---

## Monitoramento

### Ferramentas Recomendadas
- **UptimeRobot** (gratuito): Monitora uptime
- **Sentry** (gratuito até 5k eventos): Monitora erros
- **Datadog** (pago): Monitoramento completo

### Alertas
- Email quando API primária cai
- Slack/Discord quando failover ativa
- Dashboard de status público

---

## Conclusão

A melhor solução para você agora é:

1. ✅ **Deploy no Render** como backup (gratuito)
2. ✅ **Implementar failover no frontend** (2 horas)
3. ⏳ **Cloudflare Load Balancer** quando crescer

Isso te dá redundância com custo zero e proteção contra 90% dos problemas.

Quer que eu implemente o failover automático no frontend agora?
