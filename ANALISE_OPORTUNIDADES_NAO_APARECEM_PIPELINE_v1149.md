# Análise: Oportunidades Não Aparecem no Pipeline Após Criação (v1149)

## Problema Reportado
Após salvar uma nova oportunidade, ela não aparece no Pipeline de vendas.
URL: https://lwksistemas.com.br/loja/22239255889/crm-vendas/pipeline

## Análise do Código

### 1. Frontend - Criação de Oportunidade (`pipeline/page.tsx`)

**Função `handleCriarOportunidade` (linhas 165-217):**
```typescript
const payload: Record<string, unknown> = {
  lead: leadId,
  titulo: formCriar.titulo.trim(),
  valor,
  etapa: formCriar.etapa,
  valor_comissao,
};
const vendedorId = authService.getVendedorId();
if (vendedorId) payload.vendedor = vendedorId;
```

**Problema identificado:**
- O código tenta obter `vendedorId` via `authService.getVendedorId()`
- Se `vendedorId` for `null` ou `undefined`, a oportunidade é criada **SEM vendedor**
- Após criar, chama `loadOportunidades(setOportunidades, setError)` para recarregar

### 2. Backend - Filtro de Vendedor (`mixins.py`)

**VendedorFilterMixin.filter_by_vendedor (linhas 67-93):**
```python
# Construir filtro Q: vendedor OU oportunidades não atribuídas (pool compartilhado)
filters = Q(**{self.vendedor_filter_field: vendedor_id})
# Incluir registros onde o campo de vendedor é NULL (ex: oportunidade sem vendedor)
null_field = f'{self.vendedor_filter_field}__isnull'
filters |= Q(**{null_field: True})
```

**Comportamento:**
- Vendedores veem: suas oportunidades + oportunidades sem vendedor (NULL)
- Owner vê: TODAS as oportunidades (sem filtro)

### 3. Backend - Criação de Oportunidade (`views.py`)

**OportunidadeViewSet.perform_create (linhas 632-660):**
```python
def perform_create(self, serializer):
    vendedor_id = get_current_vendedor_id(self.request)
    data = serializer.validated_data
    
    # 1. Usar vendedor logado (VendedorUsuario)
    if vendedor_id is not None and not data.get('vendedor'):
        serializer.save(vendedor_id=vendedor_id)
        return
    
    # 2. Fallback: herdar vendedor do lead
    lead = data.get('lead')
    if lead and not data.get('vendedor') and getattr(lead, 'vendedor_id', None):
        serializer.save(vendedor_id=lead.vendedor_id)
        logger.info('Oportunidade criada com vendedor herdado do lead...')
        return
    
    # 3. Log quando oportunidade é criada sem vendedor
    if not data.get('vendedor') and (vendedor_id is None or not lead or not getattr(lead, 'vendedor_id', None)):
        logger.warning('Oportunidade criada SEM vendedor...')
    
    serializer.save()
```

**Lógica:**
1. Tenta usar `vendedor_id` do usuário logado (VendedorUsuario)
2. Se não tiver, herda do lead
3. Se não tiver, cria sem vendedor (NULL)

### 4. Endpoint `/crm-vendas/crm-me/` (`views.py`)

**Função `crm_me` (linhas 1050-1095):**
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crm_me(request):
    """
    Retorna o contexto do usuário logado no CRM.
    Usado pelo frontend para obter vendedor_id quando o login não o retornou.
    
    IMPORTANTE: Owner NUNCA é marcado como vendedor (is_vendedor=False), mesmo se vinculado.
    """
    loja_id = get_current_loja_id()
    vendedor_id = get_current_vendedor_id(request)
    
    # Verificar se é proprietário da loja
    is_owner = loja and loja.owner_id == request.user.id
    
    if vendedor_id is not None:
        vendedor = Vendedor.objects.filter(id=vendedor_id, loja_id=loja_id).first()
        user_display_name = vendedor.nome if vendedor else ...
        # Owner NUNCA é marcado como vendedor, mesmo se vinculado
        if not is_owner:
            user_role = 'vendedor'
            is_vendedor = True
    
    if is_owner and loja:
        owner = loja.owner
        user_display_name = ...
        user_role = 'administrador'
        is_vendedor = False
    
    return Response({
        'vendedor_id': vendedor_id,
        'is_vendedor': is_vendedor,
        'user_display_name': user_display_name,
        'user_role': user_role,
    })
```

## Diagnóstico do Problema

### Cenário 1: Owner SEM VendedorUsuario vinculado
- `authService.getVendedorId()` retorna `null`
- Oportunidade criada SEM `vendedor_id` (NULL)
- Owner vê a oportunidade (sem filtro)
- ✅ **Funciona corretamente**

### Cenário 2: Owner COM VendedorUsuario vinculado
- `authService.getVendedorId()` retorna o ID do vendedor
- Oportunidade criada COM `vendedor_id`
- Owner vê a oportunidade (sem filtro)
- ✅ **Funciona corretamente**

### Cenário 3: Vendedor comum (não-owner)
- `authService.getVendedorId()` retorna o ID do vendedor
- Oportunidade criada COM `vendedor_id`
- Vendedor vê suas oportunidades + oportunidades sem vendedor
- ✅ **Funciona corretamente**

### Cenário 4: PROBLEMA - authService não retorna vendedor_id
- `authService.getVendedorId()` retorna `null` (sessão antiga, cache, etc)
- Backend `get_current_vendedor_id()` retorna o vendedor correto
- Oportunidade criada COM `vendedor_id` (via backend)
- Frontend recarrega lista e **NÃO vê a oportunidade**
- ❌ **BUG: Frontend não tem vendedor_id atualizado no authService**

## Causa Raiz

O problema está na **sincronização entre frontend e backend**:

1. Frontend usa `authService.getVendedorId()` para enviar no payload
2. Backend usa `get_current_vendedor_id(request)` para filtrar a lista
3. Se `authService` não tiver `vendedor_id` atualizado:
   - Backend cria oportunidade com vendedor correto
   - Frontend recarrega lista SEM vendedor_id no filtro
   - Oportunidade não aparece na lista

## Soluções Propostas

### Solução 1: Garantir que authService sempre tenha vendedor_id (RECOMENDADA)
- Chamar `/crm-vendas/crm-me/` ao carregar página do pipeline
- Atualizar `authService` com `vendedor_id` retornado
- Garantir sincronização entre frontend e backend

### Solução 2: Backend sempre define vendedor_id
- Remover lógica de `vendedor` no payload do frontend
- Backend sempre usa `get_current_vendedor_id(request)`
- Simplifica lógica, mas perde flexibilidade

### Solução 3: Frontend recarrega com filtro correto
- Após criar oportunidade, chamar `/crm-vendas/crm-me/`
- Atualizar `authService` antes de recarregar lista
- Garante que filtro esteja correto

## Recomendação

**Implementar Solução 1 + Solução 3:**

1. Adicionar `useEffect` no pipeline para chamar `/crm-vendas/crm-me/` ao montar
2. Atualizar `authService` com `vendedor_id` retornado
3. Após criar oportunidade, recarregar `/crm-vendas/crm-me/` antes de `loadOportunidades()`
4. Garantir que `authService` sempre esteja sincronizado com backend

## Próximos Passos

1. ✅ Análise completa do código
2. ⏳ Implementar correção no frontend
3. ⏳ Testar cenários (owner, vendedor, sessão antiga)
4. ⏳ Deploy e validação em produção

---

**Data:** 19/03/2026  
**Versão:** v1149  
**Status:** Análise concluída, aguardando implementação
