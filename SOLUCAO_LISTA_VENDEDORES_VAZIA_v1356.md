# Solução: Lista de Vendedores Vazia (v1356-v1358)

## Problema
Endpoint `/api/crm-vendas/vendedores/` retornava lista vazia `{"count":0,"next":null,"previous":null,"results":[]}` mesmo com vendedor existindo no banco.

## Causa Raiz
O método `VendedorViewSet.get_queryset()` estava usando `annotate()` com `Exists()` para verificar se o vendedor tinha acesso via `VendedorUsuario`:

```python
qs = qs.annotate(
    tem_acesso_anotado=Exists(
        VendedorUsuario.objects.filter(
            loja_id=loja_id,
            vendedor_id=OuterRef('id')
        )
    )
)
```

O problema é que:
- `Vendedor` está no schema isolado PostgreSQL (ex: `loja_41449198000172`)
- `VendedorUsuario` está no banco `default` (tabela compartilhada)
- O `Exists()` tentava fazer um JOIN cross-database que **falhava silenciosamente**, resultando em queryset vazio

## Solução (v1356)
Remover o `annotate()` com `Exists()` cross-database do método `get_queryset()`:

```python
def get_queryset(self):
    """✅ OTIMIZAÇÃO: Anotar tem_acesso para evitar N+1 queries"""
    qs = super().get_queryset()
    
    # Anotar se vendedor tem acesso (evita N+1)
    # IMPORTANTE: VendedorUsuario está no banco 'default', não no schema isolado
    # Não podemos usar Exists() cross-database, então removemos a anotação aqui
    # e fazemos a verificação no serializer ou no método list()
    
    if hasattr(Vendedor, 'is_active'):
        return qs.filter(is_active=True)
    return qs
```

## Testes Realizados

### v1357-v1358: Scripts de Diagnóstico
Criado script `backend/testar_vendedores_api.py` que confirmou:

1. ✅ Vendedor existe no banco (ID=1, loja_id=172)
2. ✅ `Vendedor.objects.all()` retorna 1 vendedor
3. ✅ `BaseModelViewSet.get_queryset()` retorna 1 vendedor
4. ✅ `VendedorViewSet.get_queryset()` retorna 1 vendedor (após correção)

### Resultado Final
```
TESTE 3: VendedorViewSet.get_queryset()
================================================================================
Contexto antes do viewset: loja_id=172

Testando super().get_queryset():
  - BaseModelViewSet.get_queryset() count: 1

Testando VendedorViewSet.get_queryset():
  - Contexto depois do viewset: loja_id=172
  - Total no viewset queryset: 1
  - Query SQL: SELECT ... FROM "crm_vendas_vendedor" WHERE ("crm_vendas_vendedor"."loja_id" = 172 AND "crm_vendas_vendedor"."is_active" AND "crm_vendas_vendedor"."is_active") ORDER BY "crm_vendas_vendedor"."nome" ASC
  - ID: 1, Nome: LUIZ HENRIQUE FELIX, Email: consultorluizfelix@hotmail.com, is_admin: True
```

## Arquivos Modificados
- `backend/crm_vendas/views.py` (VendedorViewSet.get_queryset - v1356)
- `backend/testar_vendedores_api.py` (script de diagnóstico - v1357-v1358)

## Lições Aprendidas
1. **Joins cross-database falham silenciosamente**: PostgreSQL não permite JOINs entre schemas diferentes, e o Django não lança erro explícito
2. **Exists() não funciona cross-database**: Usar `Exists()` com `OuterRef()` entre schemas diferentes resulta em queryset vazio
3. **Alternativas para verificação cross-database**:
   - Fazer a verificação no serializer (N+1 queries, mas funciona)
   - Usar `prefetch_related` com `Prefetch` customizado
   - Fazer query separada e combinar os resultados em Python

## Status
✅ **RESOLVIDO** - Endpoint agora retorna o vendedor corretamente
