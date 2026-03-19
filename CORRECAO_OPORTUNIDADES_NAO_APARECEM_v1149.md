# Correção: Oportunidades Não Aparecem no Pipeline (v1149)

## Problema
Após criar uma nova oportunidade, ela não aparecia no Pipeline de vendas.

## Causa Raiz
Dessincronia entre `authService.getVendedorId()` (frontend) e `get_current_vendedor_id(request)` (backend):
- Frontend enviava `vendedor_id` no payload usando `authService`
- Backend filtrava lista usando `get_current_vendedor_id(request)`
- Se `authService` não tivesse `vendedor_id` atualizado, a oportunidade era criada mas não aparecia na lista

## Solução Implementada

### 1. Adicionado método `setVendedorId` ao authService (`frontend/lib/auth.ts`)
```typescript
/**
 * Define o ID do vendedor logado.
 * Usado para sincronizar vendedor_id com backend após login ou criação de oportunidade.
 */
setVendedorId(vendedorId: number): void {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('current_vendedor_id', String(vendedorId));
    sessionStorage.setItem('is_vendedor', '1');
  }
}
```

### 2. Sincronização ao montar componente Pipeline (`pipeline/page.tsx`)
```typescript
// Sincronizar vendedor_id com backend ao montar componente
useEffect(() => {
  apiClient
    .get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/crm-me/')
    .then((res) => {
      const { vendedor_id } = res.data;
      if (vendedor_id) {
        authService.setVendedorId(vendedor_id);
      }
      setVendedorIdSynced(true);
    })
    .catch(() => {
      setVendedorIdSynced(true);
    });
}, []);
```

### 3. Aguardar sincronização antes de carregar oportunidades
```typescript
useEffect(() => {
  if (!vendedorIdSynced) return;
  
  apiClient
    .get<Oportunidade[] | { results: Oportunidade[] }>('/crm-vendas/oportunidades/')
    .then((res) => setOportunidades(normalizeListResponse(res.data)))
    .catch((err) => {
      setError(err.response?.data?.detail || 'Erro ao carregar oportunidades.');
    })
    .finally(() => setLoading(false));
}, [vendedorIdSynced]);
```

### 4. Sincronização após criar oportunidade
```typescript
// Sincronizar vendedor_id antes de recarregar lista
try {
  const meRes = await apiClient.get<{ vendedor_id: number | null }>('/crm-vendas/crm-me/');
  if (meRes.data.vendedor_id) {
    authService.setVendedorId(meRes.data.vendedor_id);
  }
} catch {
  // Ignora erro de sincronização
}

setModalCriar(false);
loadOportunidades(setOportunidades, setError);
```

## Benefícios

1. **Sincronização automática**: `vendedor_id` sempre atualizado ao carregar pipeline
2. **Compatibilidade com sessões antigas**: Funciona mesmo se login não retornou `vendedor_id`
3. **Consistência**: Frontend e backend sempre usam o mesmo `vendedor_id`
4. **Sem quebra**: Owner sem vendedor vinculado continua funcionando (vendedor_id = null)

## Cenários Testados

### Cenário 1: Owner sem VendedorUsuario
- ✅ `vendedor_id` = null
- ✅ Oportunidade criada sem vendedor
- ✅ Owner vê todas as oportunidades

### Cenário 2: Owner com VendedorUsuario
- ✅ `vendedor_id` sincronizado via `/crm-me/`
- ✅ Oportunidade criada com vendedor
- ✅ Owner vê todas as oportunidades

### Cenário 3: Vendedor comum
- ✅ `vendedor_id` sincronizado via `/crm-me/`
- ✅ Oportunidade criada com vendedor
- ✅ Vendedor vê suas oportunidades + sem vendedor

### Cenário 4: Sessão antiga (sem vendedor_id no authService)
- ✅ `vendedor_id` sincronizado ao montar componente
- ✅ Oportunidade criada com vendedor correto
- ✅ Lista recarregada com filtro correto

## Arquivos Modificados

1. `frontend/lib/auth.ts`
   - Adicionado método `setVendedorId()`

2. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`
   - Adicionado estado `vendedorIdSynced`
   - Adicionado `useEffect` para sincronizar ao montar
   - Modificado `useEffect` de carregamento para aguardar sincronização
   - Adicionado sincronização após criar oportunidade

## Documentação

- `ANALISE_OPORTUNIDADES_NAO_APARECEM_PIPELINE_v1149.md`: Análise completa do problema
- `CORRECAO_OPORTUNIDADES_NAO_APARECEM_v1149.md`: Este documento

---

**Data:** 19/03/2026  
**Versão:** v1149  
**Status:** Correção implementada, pronto para deploy
