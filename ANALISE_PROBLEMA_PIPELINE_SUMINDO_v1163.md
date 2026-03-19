# Análise: Oportunidades Sumindo e Aparecendo no Pipeline (v1163)

## 🔍 Problema Identificado

As oportunidades no pipeline estão "sumindo e aparecendo" intermitentemente.

### Evidências dos Logs

```
07:44:02 GET /api/crm-vendas/oportunidades/ 200 bytes=52  (lista vazia [])
07:44:02 GET /api/crm-vendas/oportunidades/ 200 bytes=52  (lista vazia [])
07:46:03 GET /api/crm-vendas/oportunidades/ 200 bytes=437 (com dados)
```

## 🐛 Causa Raiz: Race Condition no Cache

O problema ocorre devido a uma race condition no sistema de cache:

### Fluxo Problemático

1. **Cache é invalidado** (após criar/atualizar oportunidade)
2. **Requisição A** chega, cache vazio, inicia busca no BD (demora ~50ms)
3. **Requisição B** chega 10ms depois, cache ainda vazio
4. **Requisição B** não encontra cache, retorna `[]` vazio
5. **Requisição A** termina e salva resultado no cache
6. **Próximas requisições** pegam do cache corretamente

### Por que acontece?

- Frontend faz polling a cada poucos segundos
- Múltiplas abas/usuários acessando simultaneamente
- Invalidação de cache após cada operação
- Sem lock/mutex para evitar requisições simultâneas

## 💡 Solução

### Opção 1: Cache Lock (Recomendado)
Usar lock do Redis para garantir que apenas uma requisição busque do BD por vez.

### Opção 2: Reduzir TTL do Cache
Diminuir tempo de cache de 5min para 30s, reduzindo janela de problema.

### Opção 3: Stale-While-Revalidate
Retornar cache antigo enquanto atualiza em background.

## 📝 Implementação Recomendada

Adicionar lock no decorator `cache_list_response`:

```python
def cache_list_response(cache_prefix, ttl=120, extra_keys=None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # ... código existente ...
            
            # Tentar obter do cache
            if cache_key:
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)
            
            # NOVO: Lock para evitar race condition
            lock_key = f"{cache_key}:lock"
            lock_acquired = cache.add(lock_key, "1", timeout=10)
            
            if not lock_acquired:
                # Outra requisição está buscando, aguardar um pouco
                import time
                time.sleep(0.1)
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)
            
            try:
                # Executar função original
                response = func(self, request, *args, **kwargs)
                
                # Cachear se sucesso
                if cache_key and response.status_code == 200:
                    cache.set(cache_key, response.data, ttl)
                
                return response
            finally:
                if lock_acquired:
                    cache.delete(lock_key)
        return wrapper
    return decorator
```

## ⚠️ Impacto

- **Baixo risco**: Apenas adiciona lock, não muda lógica
- **Performance**: Melhora (evita múltiplas queries simultâneas)
- **UX**: Elimina efeito de "sumindo e aparecendo"

## 🧪 Testes

1. Abrir pipeline em múltiplas abas
2. Criar nova oportunidade
3. Verificar se todas as abas atualizam corretamente
4. Não deve haver "piscadas" ou listas vazias

## Status

⏳ **AGUARDANDO APROVAÇÃO** - Solução identificada, aguardando implementação
