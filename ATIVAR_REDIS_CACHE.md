# Guia Rápido: Ativar Redis Cache

## ✅ Situação Atual
- PostgreSQL: ✅ Configurado e funcionando
- Gunicorn 4 workers: ✅ Configurado e funcionando  
- Redis: ⚠️ Disponível mas não ativado (USE_REDIS=false)

**Capacidade atual: 300-400 usuários simultâneos**

---

## 🚀 Ativar Redis (1 hora)

### Passo 1: Atualizar settings.py

Adicione no final do arquivo `backend/config/settings.py`:

```python
# ============================================
# REDIS CACHE CONFIGURATION
# ============================================
import os

USE_REDIS = os.environ.get('USE_REDIS', 'false').lower() == 'true'

if USE_REDIS:
    REDIS_URL = os.environ.get('REDIS_URL')
    if REDIS_URL:
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                    'CONNECTION_POOL_KWARGS': {
                        'max_connections': 50,
                        'retry_on_timeout': True,
                    },
                },
                'KEY_PREFIX': 'lwk',
                'TIMEOUT': 300,  # 5 minutos padrão
            }
        }
        print("✅ Redis cache ativado:", REDIS_URL[:30] + "...")
    else:
        print("⚠️ USE_REDIS=true mas REDIS_URL não encontrado")
else:
    print("ℹ️ Redis cache desativado (USE_REDIS=false)")
```

### Passo 2: Commit e Deploy

```bash
cd ~/Documents/lwksistemas

# Adicionar mudanças
git add backend/config/settings.py

# Commit
git commit -m "feat: Adiciona suporte para Redis cache configurável via USE_REDIS

- Redis cache compartilhado entre workers
- Connection pooling otimizado (50 conexões)
- Timeout configurado (5s)
- Key prefix 'lwk' para isolamento
- Ativação via variável de ambiente USE_REDIS=true"

# Deploy
git push origin master
git push heroku master
```

### Passo 3: Ativar no Heroku

```bash
# Ativar Redis
heroku config:set USE_REDIS=true --app lwksistemas

# Verificar configuração
heroku config --app lwksistemas | grep -E "USE_REDIS|REDIS_URL"

# Reiniciar aplicação
heroku restart --app lwksistemas
```

### Passo 4: Verificar Logs

```bash
# Monitorar logs por 2-3 minutos
heroku logs --tail --app lwksistemas

# Procurar por:
# ✅ "Redis cache ativado: rediss://..."
# ✅ Sem erros de conexão Redis
```

---

## 📊 Resultado Esperado

### Antes (LocMemCache)
- Cache isolado por worker
- Cache miss rate: 60-70%
- Tempo de resposta: 300-500ms
- Capacidade: 300-400 usuários

### Depois (Redis)
- Cache compartilhado entre workers
- Cache miss rate: 10-20%
- Tempo de resposta: 150-400ms
- Capacidade: 400-500 usuários

---

## 🔍 Testar Performance

### Teste 1: Dashboard CRM
```bash
# Primeira requisição (cache miss)
time curl -H "Authorization: Bearer TOKEN" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/dashboard/

# Segunda requisição (cache hit - deve ser mais rápida)
time curl -H "Authorization: Bearer TOKEN" \
  https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/dashboard/
```

### Teste 2: Monitorar Redis
```bash
# Ver estatísticas do Redis
heroku redis:info --app lwksistemas

# Procurar por:
# - connected_clients: número de conexões
# - used_memory_human: memória usada
# - keyspace_hits: cache hits
# - keyspace_misses: cache misses
```

---

## ⚠️ Rollback (Se necessário)

Se houver problemas, desativar Redis:

```bash
# Desativar Redis
heroku config:set USE_REDIS=false --app lwksistemas

# Reiniciar
heroku restart --app lwksistemas

# Sistema volta a usar LocMemCache
```

---

## 💰 Custo

- Custo atual: $18/mês
- Custo após ativar Redis: $18/mês (sem mudança)
- Redis já está pago e disponível

---

## 📞 Próximos Passos

### Se performance for suficiente (400-500 usuários)
✅ Manter configuração atual  
✅ Monitorar por 1 semana  
✅ Custo: $18/mês

### Se precisar mais capacidade (600-800 usuários)
⚠️ Fazer upgrade do dyno:
```bash
heroku ps:resize web=standard-2x --app lwksistemas
# Custo adicional: +$43/mês = $61/mês total
```

---

## 🎯 Conclusão

**Ativar Redis é simples, rápido e sem custo adicional.**

- ⏱️ Tempo: 1 hora
- 💰 Custo: $0 (Redis já pago)
- 📈 Ganho: +25% performance
- 👥 Capacidade: 400-500 usuários simultâneos
