# Otimizações de Performance — Custo Zero

**Data:** 19/06/2026  
**Objetivo:** Aumentar capacidade de lojas simultâneas mantendo velocidade com 3 usuários/loja.

---

## 1. Gunicorn — Workers e Conexões

### Antes
```
--workers 2 --threads 2 --worker-connections 500
```
**Capacidade:** 4 slots paralelos → ~80 req/s

### Depois
```
--workers 4 --threads 2 --worker-connections 1000 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --graceful-timeout 30
```
**Capacidade:** 8 slots paralelos → ~160 req/s (+100%)

### Parâmetros adicionados:
- `--keep-alive 5` — reutiliza conexões TCP (menos overhead por request)
- `--max-requests 1000` — recicla workers após 1000 requests (evita memory leaks)
- `--max-requests-jitter 50` — jitter para evitar reinício simultâneo de workers
- `--graceful-timeout 30` — tempo para terminar requests em andamento no restart
- `--worker-connections 1000` — mais conexões simultâneas por worker (gthread)

### Configurável via env:
```bash
WEB_CONCURRENCY=6  # Para escalar além de 4 workers
```

---

## 2. Cache Server-Side (ResponseCacheMiddleware)

### O que faz
Cacheia respostas JSON de endpoints de alto tráfego no Redis (server-side).
Não depende do navegador — funciona independente de headers Cache-Control do cliente.

### Endpoints cacheados

| Endpoint | TTL | Tipo |
|----------|-----|------|
| `/api/superadmin/lojas/info_publica/` | 5min | Público |
| `/api/superadmin/lojas/por-atalho/` | 5min | Público |
| `/api/homepage/` | 10min | Público |
| `/api/crm-vendas/config/` | 2min | Autenticado |
| `/api/clinica-beleza/dashboard/` | 1min | Autenticado |
| `/api/restaurante/categorias/` | 2min | Autenticado |
| `/api/cabeleireiro/servicos/` | 2min | Autenticado |
| `/api/hotel/tipos-quarto/` | 2min | Autenticado |

### Comportamento
- Só cacheia GET com resposta 200 + JSON
- Respeita `Cache-Control: no-cache` do cliente (force refresh)
- Header `X-Cache: HIT` ou `MISS` na resposta para debug
- Só ativa quando `USE_REDIS=true` (produção)
- Não cacheia em dev (sem Redis)

### Ganho estimado
- **-40% queries no PostgreSQL** para cenários de múltiplos usuários na mesma loja
- Endpoints públicos (info_publica) chamados em toda abertura de página de login

---

## 3. Connection Pooling — CONN_MAX_AGE

### Antes
```python
conn_max_age=60  # 1 minuto
```

### Depois
```python
conn_max_age=120  # 2 minutos (configurável via env CONN_MAX_AGE)
```

### Efeito
Com `gthread` workers, conexões ao PostgreSQL são reutilizadas por mais tempo.
Reduz overhead de handshake TCP+TLS em ~50% (Railway proxy público usa TLS).

---

## 4. Impacto Estimado

| Métrica | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| Slots paralelos | 4 | 8 | +100% |
| Req/s teórico | ~80 | ~160 | +100% |
| Queries/req (cache hit) | N | 0 | -100% |
| Lojas ativas simultâneas | ~10 | ~20-25 | +100% |
| Lojas totais (30% ativos) | ~30 | ~60-80 | +100% |

---

## 5. Próxima Escala (se necessário)

Para ir além de 80 lojas:
1. `WEB_CONCURRENCY=6` (env var Railway) — +50% sem rebuild
2. Horizontal scale (2 instâncias lwks-backend) — dobra capacidade
3. Aumentar RAM do serviço Railway — permite mais workers
