# Análise: Problema Recorrente de Cache no CRM Vendas

**Data**: 23/03/2026  
**Versão Atual**: v1276 → v1277  
**Status**: RESOLVIDO

---

## 🔴 PROBLEMA

Dados não aparecem imediatamente após criação/atualização em várias telas do CRM:
- ✅ Pipeline de Vendas (Oportunidades) - RESOLVIDO v1276
- ❌ Contas (Customers) - NÃO APARECE
- ❌ Leads
- ❌ Contatos
- ❌ Atividades

**Sintomas**:
- Registro criado mas não aparece na lista
- Após F5 (refresh), registro aparece
- Problema recorrente em todas as telas com cache

---

## 🔍 CAUSA RAIZ

### Cache de 5 minutos em TODOS os ViewSets
```python
# ANTES (v1275)
@cache_list_response(CRMCacheManager.CONTAS, ttl=300)      # 5 minutos!
@cache_list_response(CRMCacheManager.LEADS, ttl=300)       # 5 minutos!
@cache_list_response(CRMCacheManager.CONTATOS, ttl=300)    # 5 minutos!
@cache_list_response(CRMCacheManager.ATIVIDADES, ttl=300)  # 5 minutos!
@cache_list_response(CRMCacheManager.OPORTUNIDADES, ttl=300)  # 5 minutos!
```

**Problema**: TTL de 300 segundos (5 minutos) é muito longo para dados que mudam frequentemente.

---

## ✅ SOLUÇÃO IMPLEMENTADA

### Reduzir TTL de 5min para 30s em TODOS os ViewSets + Headers no-cache

```python
# DEPOIS (v1277)
@cache_list_response(CRMCacheManager.CONTAS, ttl=30)  # ✅ 30 segundos
def list(self, request, *args, **kwargs):
    response = super().list(request, *args, **kwargs)
    # Adicionar headers para evitar cache do navegador
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
```

**Aplicado em**:
- ✅ ContaViewSet (Contas/Customers)
- ✅ LeadViewSet (Leads)
- ✅ ContatoViewSet (Contatos)
- ✅ AtividadeViewSet (Atividades)
- ✅ OportunidadeViewSet (Pipeline) - já corrigido v1276

---

## 📊 FLUXO CORRETO APÓS CORREÇÃO

### Criar Conta/Lead/Contato/Atividade
1. Frontend envia POST `/api/crm-vendas/{recurso}/`
2. ViewSet cria registro
3. `CacheInvalidationMixin` invalida cache automaticamente
4. `CRMCacheManager.invalidate()` deleta cache de todos os vendedores
5. Próximo GET retorna dados atualizados do banco (cache foi invalidado)

### Listar Registros
1. Frontend envia GET `/api/crm-vendas/{recurso}/`
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
- ViewSets afetados: 5 (Contas, Leads, Contatos, Atividades, Oportunidades)

### v1276
- TTL: 30s apenas em Oportunidades
- Invalidação: ✅ Funciona
- Tempo para aparecer: Imediato em Oportunidades
- ViewSets afetados: 4 (Contas, Leads, Contatos, Atividades ainda com 5min)

### Depois (v1277)
- TTL: 30s (30 segundos) em TODOS
- Invalidação: ✅ Funciona corretamente
- Tempo para aparecer: Imediato em TODOS
- ViewSets corrigidos: 5 (100%)

---

## 🔧 ARQUIVOS MODIFICADOS

### v1276
1. `backend/crm_vendas/cache.py`
   - Adicionado método `invalidate()` genérico

2. `backend/crm_vendas/mixins.py`
   - Corrigido `_invalidate_caches()` para obter `loja_id`

3. `backend/crm_vendas/views.py`
   - Reduzido TTL de 300s para 30s no `OportunidadeViewSet.list()`

### v1277
1. `backend/crm_vendas/views.py`
   - Reduzido TTL de 300s para 30s em:
     - `ContaViewSet.list()`
     - `LeadViewSet.list()`
     - `ContatoViewSet.list()`
     - `AtividadeViewSet.list()`
   - Adicionado headers no-cache em todos

---

## ✅ TESTES REALIZADOS

### v1276 (Oportunidades)
1. ✅ Criar oportunidade → Aparece imediatamente
2. ✅ Atualizar oportunidade → Mudanças aparecem imediatamente
3. ✅ Deletar oportunidade → Some imediatamente

### v1277 (Todos os recursos)
1. ✅ Criar conta → Aparece imediatamente
2. ✅ Criar lead → Aparece imediatamente
3. ✅ Criar contato → Aparece imediatamente
4. ✅ Criar atividade → Aparece imediatamente
5. ✅ Cache ainda funciona (performance mantida)
6. ✅ Múltiplos vendedores veem dados corretos

---

## 📝 CONCLUSÃO

O problema era cache de 5 minutos em TODOS os ViewSets do CRM. A correção v1276 resolveu apenas Oportunidades.

A solução completa (v1277):
1. Reduzir TTL para 30 segundos em TODOS os ViewSets
2. Adicionar headers no-cache em TODOS os list()
3. Manter invalidação automática funcionando (v1276)

**Resultado**: Todos os dados do CRM agora aparecem imediatamente após criação/atualização/deleção, mantendo benefícios de performance do cache (30s).
