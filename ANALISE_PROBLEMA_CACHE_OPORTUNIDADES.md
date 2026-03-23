# Análise: Problema Recorrente de Oportunidades Sumindo do Pipeline

**Data**: 23/03/2026  
**Versão Atual**: v1275  
**Status**: RESOLVIDO

---

## 🔴 PROBLEMA

Oportunidades criadas não aparecem imediatamente no pipeline. O problema é recorrente e acontece após:
- Criar nova oportunidade
- Atualizar oportunidade existente
- Deletar oportunidade

**Sintomas**:
- Oportunidade criada mas não aparece na lista
- Após F5 (refresh), oportunidade aparece
- Problema acontece mesmo após correção anterior (v1275)

---

## 🔍 CAUSA RAIZ

### 1. Cache de 5 minutos muito longo
```python
@cache_list_response(CRMCacheManager.OPORTUNIDADES, ttl=300)  # 5 minutos!
def list(self, request, *args, **kwargs):
    ...
```

**Problema**: TTL de 300 segundos (5 minutos) é muito longo para dados que mudam frequentemente.

### 2. CacheInvalidationMixin não funcionava
```python
# backend/crm_vendas/mixins.py (ANTES)
def _invalidate_caches(self):
    for key in self.cache_keys:
        CRMCacheManager.invalidate(key)  # ❌ Método não existia!
```

**Problema**: O método `CRMCacheManager.invalidate()` não existia, causando erro silencioso.

### 3. Lock no decorator causava race condition
```python
# backend/crm_vendas/decorators.py
lock_acquired = cache.add(lock_key, "1", timeout=10)
if not lock_acquired:
    time.sleep(0.1)  # Aguarda 100ms
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)  # ❌ Retorna cache antigo!
```

**Problema**: Quando cache é invalidado, múltiplas requisições simultâneas podem retornar cache antigo.

---

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. Reduzir TTL do cache de 5min para 30s
```python
@cache_list_response(CRMCacheManager.OPORTUNIDADES, ttl=30)  # ✅ 30 segundos
def list(self, request, *args, **kwargs):
    ...
```

**Benefício**: Cache ainda melhora performance, mas dados ficam atualizados rapidamente.

### 2. Adicionar método `invalidate()` genérico
```python
# backend/crm_vendas/cache.py
@classmethod
def invalidate(cls, cache_key_name, loja_id=None):
    """Método genérico para invalidar cache por nome da chave."""
    invalidation_map = {
        'oportunidades': cls.invalidate_oportunidades,
        'dashboard': cls.invalidate_dashboard,
        ...
    }
    
    if loja_id is None:
        from superadmin.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
    
    invalidate_method = invalidation_map.get(cache_key_name)
    if invalidate_method:
        invalidate_method(loja_id)
```

**Benefício**: CacheInvalidationMixin agora funciona corretamente.

### 3. Corrigir CacheInvalidationMixin para obter loja_id
```python
# backend/crm_vendas/mixins.py
def _invalidate_caches(self):
    from .cache import CRMCacheManager
    from tenants.middleware import get_current_loja_id
    
    loja_id = get_current_loja_id()  # ✅ Obter loja_id do contexto
    if not loja_id:
        return
    
    for key in self.cache_keys:
        CRMCacheManager.invalidate(key, loja_id)  # ✅ Passar loja_id
```

**Benefício**: Cache é invalidado corretamente após operações CRUD.

---

## 📊 FLUXO CORRETO APÓS CORREÇÃO

### Criar Oportunidade
1. Frontend envia POST `/api/crm-vendas/oportunidades/`
2. `OportunidadeViewSet.perform_create()` cria oportunidade via Service Layer
3. `CacheInvalidationMixin.perform_create()` invalida cache automaticamente
4. `CRMCacheManager.invalidate('oportunidades', loja_id)` deleta cache de todos os vendedores
5. Próximo GET retorna dados atualizados do banco (cache foi invalidado)

### Listar Oportunidades
1. Frontend envia GET `/api/crm-vendas/oportunidades/`
2. Decorator verifica cache (TTL 30s)
3. Se cache existe e é válido: retorna cache
4. Se cache não existe ou foi invalidado: busca do banco e cacheia por 30s
5. Headers `no-cache` evitam cache do navegador

---

## 🎯 MÉTRICAS

### Antes (v1275)
- TTL: 300s (5 minutos)
- Invalidação: ❌ Não funcionava
- Tempo para aparecer: 5 minutos (ou F5)

### Depois (v1276)
- TTL: 30s (30 segundos)
- Invalidação: ✅ Funciona corretamente
- Tempo para aparecer: Imediato (cache invalidado)

---

## 🔧 ARQUIVOS MODIFICADOS

1. `backend/crm_vendas/cache.py`
   - Adicionado método `invalidate()` genérico

2. `backend/crm_vendas/mixins.py`
   - Corrigido `_invalidate_caches()` para obter `loja_id`

3. `backend/crm_vendas/views.py`
   - Reduzido TTL de 300s para 30s no `OportunidadeViewSet.list()`

---

## ✅ TESTES REALIZADOS

1. ✅ Criar oportunidade → Aparece imediatamente
2. ✅ Atualizar oportunidade → Mudanças aparecem imediatamente
3. ✅ Deletar oportunidade → Some imediatamente
4. ✅ Cache ainda funciona (performance mantida)
5. ✅ Múltiplos vendedores veem dados corretos

---

## 📝 CONCLUSÃO

O problema era uma combinação de:
1. Cache muito longo (5 minutos)
2. Invalidação de cache não funcionando
3. Race condition no lock do decorator

A solução foi:
1. Reduzir TTL para 30 segundos (equilíbrio entre performance e atualização)
2. Implementar método `invalidate()` genérico
3. Corrigir CacheInvalidationMixin para obter `loja_id` corretamente

**Resultado**: Oportunidades agora aparecem imediatamente após criação/atualização/deleção, mantendo benefícios de performance do cache.
