# Projeção de Crescimento: 120 Lojas × 5 Funcionários

**Cenário:** 120 lojas, cada uma com 5 funcionários usando o app simultaneamente.  
**Total:** até **600 usuários concorrentes**.

---

## 1. Resumo Executivo

| Métrica | Atual | Recomendado (120 lojas) |
|---------|-------|--------------------------|
| Usuários simultâneos | ~30–50 | 600 |
| Workers Gunicorn | 4 | 4–6 |
| Threads por worker | 4 | 4 |
| Conexões PostgreSQL | ~20 (Basic) | 120+ (Standard) |
| Redis | Opcional | **Obrigatório** |
| CONN_MAX_AGE | 60s | 60s (manter) |

---

## 2. Capacidade Máxima de Lojas (estrutura atual)

Com a configuração atual (4 workers, PostgreSQL Essential/Standard, Redis opcional):

| Cenário | Lojas máx. | Usuários simultâneos | Observação |
|---------|------------|----------------------|------------|
| **Confortável** | **30–40** | ~150–200 (5 por loja) | Velocidade boa, margem de segurança |
| **Limite prático** | **50–60** | ~250–300 | Pode haver fila em picos |
| **Máximo teórico** | **80–100** | ~400–500 | Exige PostgreSQL Standard + Redis |

### Gargalos principais

1. **Requisições simultâneas:** 16 req = ~16 usuários atendidos ao mesmo tempo. Com 15–20% de usuários ativos em pico, 16 ÷ 0,2 ≈ 80 usuários totais.
2. **Conexões PostgreSQL:** Gunicorn (16) + Django-Q (4) + Render (8) ≈ 28 conexões. Essential (20) é insuficiente; Standard (200) suporta 60+ lojas.
3. **Segurança:** Independente do número de lojas (JWT, CORS, isolamento por schema).

### Recomendações por faixa

| Lojas | Ação | Custo aprox. |
|-------|------|---------------|
| **Até 30** | Manter como está (4 workers) | Atual |
| **30–60** | PostgreSQL Standard + Redis + 6 workers | +~$50/mês |
| **60–120** | + 2 dynos ou PgBouncer | +~$50/mês |
| **120+** | Escalar horizontalmente (mais dynos) | Variável |

---

## 3. Infraestrutura Atual (Heroku, Render, Vercel)

### 3.1 Heroku (Backend primário)

- **Procfile:** `gunicorn --workers 4 --threads 4` → 16 requisições simultâneas
- **PostgreSQL:** plano Basic (~20 conexões) ou Standard (~120)
- **Redis:** Heroku Redis (se `REDIS_URL` configurado)

### 3.2 Render (Backend backup)

- **Workers:** 2
- **Timeout:** 120s
- **Banco:** mesmo PostgreSQL do Heroku

### 3.3 Vercel (Frontend)

- Serverless; escala automaticamente.
- Não é gargalo para 600 usuários.

---

## 4. Gargalos e Recomendações

### 4.1 Backend (Gunicorn)

**Problema:** 4 workers × 4 threads = **16 requisições simultâneas**.  
Para 600 usuários, a fila cresce; para 120 lojas recomenda-se 6 workers.

**Solução:**

```
# Procfile (atual)
web: ... --workers 4 --threads 4 ...

# Recomendado para 120 lojas
web: ... --workers 4 --threads 4 ...
# ou
web: ... --workers 6 --threads 4 ...
```

- **4 workers:** ~16 requisições simultâneas (mínimo aceitável)
- **6 workers:** ~24 requisições simultâneas (recomendado)

### 4.2 PostgreSQL

**Problema:** Cada worker/thread pode manter 1 conexão (CONN_MAX_AGE=60).  
4 workers × 4 threads = 16 conexões. 6 workers = 24 conexões.

**Recomendação:**

- **Heroku Postgres Standard-0** ou superior (120 conexões)
- Ou **PgBouncer** (add-on) para connection pooling

### 4.3 Redis

**Problema:** Sem Redis, o cache usa `LocMemCache` (por processo).  
Cada worker tem seu próprio cache; não há compartilhamento.

**Recomendação:** **Heroku Redis** (ou equivalente) obrigatório para:

- Cache compartilhado entre workers
- Sessões (se migrar de DB para Redis)
- Django-Q (task queue) – já configurado para ORM, mas Redis melhora

### 4.4 Django-Q

- **Workers:** `DJANGO_Q_WORKERS=4` (atual)
- Para 120 lojas: considerar **6–8 workers** para backups e jobs em background

---

## 5. Plano de Ação

### Fase 1 – Imediato (sem custo extra)

1. **Aumentar workers no Procfile:** `--workers 4`
2. **Garantir Redis:** `REDIS_URL` configurado no Heroku
3. **Monitorar:** Heroku Metrics (response time, throughput)

### Fase 2 – Antes de 60 lojas

1. **PostgreSQL Standard** (120 conexões)
2. **Workers:** `--workers 6`
3. **CONN_MAX_AGE:** manter 60s (evita “too many connections”)

### Fase 3 – 120 lojas

1. **Escalar dynos:** considerar 2 dynos (duplicar capacidade)
2. **PgBouncer:** se conexões ainda forem gargalo
3. **CDN:** Vercel já entrega estáticos; API continua no Heroku

---

## 6. Otimizações de Código (aplicadas)

- **Paginação:** `PAGE_SIZE=50` (já configurado)
- **GZip:** habilitado no middleware
- **Whitenoise:** estáticos comprimidos
- **CORS preflight cache:** 24h
- **JWT:** access token 1h, refresh 7 dias

### Sugestões adicionais

- **select_related / prefetch_related:** em listagens com FKs
- **Índices:** em colunas usadas em filtros (`loja_id`, `created_at`, etc.)
- **Cache de queries:** para dados pouco alterados (ex.: tipos de loja)

---

## 7. Estimativa de Custo (Heroku)

| Recurso | Plano | Conexões | Custo aprox. |
|---------|-------|----------|--------------|
| Dyno | Standard-1X | - | ~$25/mês |
| PostgreSQL | Standard-0 | 120 | ~$50/mês |
| Redis | Premium-0 | - | ~$15/mês |
| **Total** | | | **~$90/mês** |

*(Valores aproximados; conferir preços atuais no Heroku.)*

---

## 8. Checklist de Deploy para 120 Lojas

- [ ] `Procfile`: `--workers 4` (mínimo) ou `--workers 6`
- [ ] `REDIS_URL` configurado no Heroku e Render
- [ ] PostgreSQL Standard ou superior
- [ ] `CONN_MAX_AGE=60` (não aumentar sem PgBouncer)
- [ ] `DJANGO_Q_WORKERS=6` para tarefas em background
- [ ] Monitorar Heroku Metrics e logs de erro

---

*Documento gerado para o projeto LWK Sistemas – projeção 120 lojas × 5 funcionários.*
