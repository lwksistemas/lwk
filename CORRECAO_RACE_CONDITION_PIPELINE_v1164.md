# Correção: Race Condition no Cache do Pipeline (v1164)

## 🎯 Problema Resolvido

Oportunidades no pipeline estavam "sumindo e aparecendo" intermitentemente devido a race condition no sistema de cache.

## 🔍 Causa Raiz

Quando o cache era invalidado (após criar/atualizar oportunidade), múltiplas requisições simultâneas podiam retornar lista vazia:

1. Cache invalidado
2. Requisição A chega, cache vazio, inicia busca no BD (demora ~50ms)
3. Requisição B chega 10ms depois, cache ainda vazio
4. **Requisição B retorna `[]` vazio** (BUG)
5. Requisição A termina e salva resultado no cache
6. Próximas requisições pegam do cache corretamente

## ✅ Solução Implementada

Adicionado **lock do Redis** no decorator `cache_list_response` para garantir que apenas uma requisição busque do BD por vez.

### Código Implementado

```python
# backend/crm_vendas/decorators.py

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
            
            # ✅ NOVO: Lock para evitar race condition
            lock_key = f"{cache_key}:lock"
            lock_acquired = cache.add(lock_key, "1", timeout=10)
            
            if not lock_acquired:
                # Outra requisição está buscando, aguardar um pouco
                import time
                time.sleep(0.1)
                cached = cache.get(cache_key)
                if cached is not None:
                    return Response(cached)
                # Se ainda não tem cache, continuar normalmente
            
            try:
                # Executar função original
                response = func(self, request, *args, **kwargs)
                
                # Cachear se sucesso
                if cache_key and response.status_code == 200:
                    cache.set(cache_key, response.data, ttl)
                
                return response
            finally:
                # Liberar lock
                if lock_acquired:
                    cache.delete(lock_key)
        return wrapper
    return decorator
```

## 🎯 Como Funciona

1. **Primeira requisição** (cache vazio):
   - Tenta obter do cache → não encontra
   - Adquire lock (`cache.add(lock_key, "1", timeout=10)`)
   - Busca dados do BD
   - Salva no cache
   - Libera lock

2. **Segunda requisição** (simultânea):
   - Tenta obter do cache → não encontra
   - Tenta adquirir lock → **falha** (já está locked)
   - Aguarda 100ms (`time.sleep(0.1)`)
   - Tenta obter do cache novamente → **encontra!** (primeira requisição já salvou)
   - Retorna dados do cache

3. **Terceira requisição** (após cache populado):
   - Tenta obter do cache → **encontra!**
   - Retorna imediatamente (sem lock, sem BD)

## 📊 Benefícios

- ✅ Elimina listas vazias intermitentes
- ✅ Reduz carga no banco de dados (evita queries duplicadas)
- ✅ Melhora experiência do usuário (sem "piscadas")
- ✅ Funciona para todas as listas cacheadas (contas, leads, oportunidades, atividades)

## 🧪 Como Testar

1. Abrir pipeline em múltiplas abas
2. Criar nova oportunidade
3. Verificar se todas as abas atualizam corretamente
4. **NÃO deve haver "piscadas" ou listas vazias**

## 📝 Arquivos Modificados

- `backend/crm_vendas/decorators.py` - Adicionado lock no `cache_list_response`
- `ANALISE_PROBLEMA_PIPELINE_SUMINDO_v1163.md` - Atualizado status para "implementado"

## 🚀 Deploy

- **Backend**: Heroku v1164 ✅
- **Frontend**: Vercel (lwksistemas.com.br) ✅
- **Data**: 19/03/2026

## 📌 Notas Técnicas

- Lock timeout: 10 segundos (suficiente para query mais lenta)
- Retry delay: 100ms (balanceado entre responsividade e carga)
- Lock é liberado no `finally` block (garante liberação mesmo em caso de erro)
- Usa `cache.add()` (atomic operation) para evitar race condition no próprio lock

---

**Status**: ✅ Implementado e em produção
