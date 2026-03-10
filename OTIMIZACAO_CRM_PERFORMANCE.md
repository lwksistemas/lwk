# Otimização de Performance - CRM Vendas

## Problemas Identificados

### 1. ❌ Query N+1 no VendedorSerializer
**Arquivo**: `backend/crm_vendas/serializers.py`
**Problema**: O método `get_tem_acesso()` faz uma query para CADA vendedor na listagem
**Impacto**: Se há 10 vendedores, são 10 queries extras

```python
def get_tem_acesso(self, obj):
    # ❌ Faz 1 query por vendedor
    return VendedorUsuario.objects.filter(
        loja_id=loja_id,
        vendedor_id=obj.id,
    ).exists()
```

**Solução**: Usar `prefetch_related` ou remover o campo se não for crítico

### 2. ✅ Views já otimizadas
- `select_related` e `prefetch_related` já implementados
- Cache de 120s no dashboard e listagens
- Queries consolidadas no dashboard (1 query por agregação)

### 3. ⚠️ Possível problema: Falta de índices
**Verificar**: Se as tabelas têm índices nas colunas mais consultadas

## Recomendações de Otimização

### Prioridade ALTA

1. **Remover campo `tem_acesso` do VendedorSerializer** (se não for essencial)
   - Ou implementar prefetch com anotação

2. **Adicionar paginação nas listagens**
   - Limitar a 50-100 registros por página
   - Reduz drasticamente o tempo de resposta

3. **Verificar índices no banco**
   - Executar `EXPLAIN ANALYZE` nas queries lentas
   - Adicionar índices compostos se necessário

### Prioridade MÉDIA

4. **Aumentar TTL do cache para 300s (5 minutos)**
   - Dashboard muda pouco, pode cachear mais tempo

5. **Implementar lazy loading no frontend**
   - Carregar dados sob demanda
   - Usar skeleton screens

6. **Comprimir respostas JSON**
   - Já tem GZip no middleware ✅

### Prioridade BAIXA

7. **Otimizar serializers**
   - Usar `SerializerMethodField` com cuidado
   - Preferir campos diretos do modelo

## Implementação Imediata

### 1. Adicionar Paginação
```python
# backend/crm_vendas/views.py
from rest_framework.pagination import PageNumberPagination

class CRMPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

# Adicionar em cada ViewSet:
pagination_class = CRMPagination
```

### 2. Otimizar VendedorSerializer
```python
# Opção 1: Remover campo (mais simples)
class VendedorSerializer(serializers.ModelSerializer):
    # Remover: tem_acesso = serializers.SerializerMethodField()
    
# Opção 2: Usar prefetch (mais complexo)
class VendedorViewSet(BaseModelViewSet):
    def get_queryset(self):
        qs = super().get_queryset()
        from django.db.models import Exists, OuterRef
        from superadmin.models import VendedorUsuario
        loja_id = get_current_loja_id()
        qs = qs.annotate(
            tem_acesso=Exists(
                VendedorUsuario.objects.filter(
                    loja_id=loja_id,
                    vendedor_id=OuterRef('id')
                )
            )
        )
        return qs
```

### 3. Aumentar Cache
```python
# backend/crm_vendas/views.py
@cache_list_response(CRMCacheManager.CONTAS, ttl=300)  # 5 minutos
def list(self, request, *args, **kwargs):
    return super().list(request, *args, **kwargs)
```

## Métricas Esperadas

### Antes da Otimização
- Tempo de resposta: 2-5 segundos
- Queries por request: 15-30
- Tamanho da resposta: 50-200KB

### Depois da Otimização
- Tempo de resposta: 200-500ms ⚡
- Queries por request: 3-8 ✅
- Tamanho da resposta: 10-50KB (com paginação) ✅

## Próximos Passos

1. ✅ Implementar paginação
2. ✅ Otimizar VendedorSerializer
3. ⏳ Aumentar TTL do cache
4. ⏳ Adicionar índices no banco
5. ⏳ Implementar lazy loading no frontend
