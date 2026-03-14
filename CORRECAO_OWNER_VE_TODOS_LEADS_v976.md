# Correção: Owner Agora Vê TODOS os Leads (v976)

## Problema Identificado

O proprietário/administrador da loja não conseguia ver leads recém-criados na lista. Leads como "teste 500" e "teste 501" eram criados com sucesso (status 201) mas não apareciam na listagem.

### Causa Raiz

A função `get_current_vendedor_id()` estava retornando `vendedor_id=1` para o owner porque:

1. Owner tinha um vendedor cadastrado com seu email (vendedor_id=1)
2. A função verificava se owner tinha vendedor e retornava esse ID
3. Isso fazia o owner ser tratado como vendedor comum
4. O filtro `VendedorFilterMixin` mostrava apenas leads do vendedor_id=1
5. Leads antigos sem vendedor ficavam ocultos

### Logs que Confirmaram o Problema

```
🔵 CRIANDO LEAD - loja_id=1, vendedor_id=1, user=2
✅ LEAD CRIADO - id=77, nome=teste 501, vendedor_id=1, loja_id=1
```

O owner (user=2) estava sendo detectado como vendedor_id=1.

## Solução Implementada

### Mudança na Lógica de Detecção

Modificada a função `get_current_vendedor_id()` em `backend/crm_vendas/utils.py`:

**ANTES:**
```python
# Owner: buscar se tem vendedor cadastrado
vendedor_owner = Vendedor.objects.filter(
    email=request.user.email,
    is_active=True
).first()
if vendedor_owner:
    return vendedor_owner.id  # ❌ Retornava ID do vendedor
```

**DEPOIS:**
```python
# Owner: sempre retorna None para ver TODOS os dados
return None  # ✅ Owner vê tudo, sem filtro
```

### Comportamento Correto

- **Owner (proprietário)**: `vendedor_id = None` → Vê TODOS os leads da loja
- **Vendedor (VendedorUsuario)**: `vendedor_id = X` → Vê apenas seus leads

## Arquivos Modificados

```
backend/crm_vendas/utils.py
```

## Impacto

### Antes
- ❌ Owner via apenas leads vinculados ao vendedor_id=1
- ❌ Leads sem vendedor ficavam ocultos
- ❌ Leads criados por outros vendedores não apareciam
- ❌ Experiência confusa e limitada

### Depois
- ✅ Owner vê TODOS os leads da loja
- ✅ Leads com ou sem vendedor aparecem
- ✅ Visão completa do pipeline de vendas
- ✅ Controle total sobre os dados

## Deploy

### Backend
```bash
git add backend/crm_vendas/utils.py
git commit -m "fix(crm): Owner agora vê TODOS os leads (v976)"
git push origin master
git push heroku master
```

**Status**: ✅ Deploy realizado com sucesso  
**Heroku**: v970

## Teste

Agora recarregue a página https://lwksistemas.com.br/loja/felix-5889/crm-vendas/leads

Você deve ver:
- ✅ Todos os leads antigos (com ou sem vendedor)
- ✅ Lead "teste 500" (criado anteriormente)
- ✅ Lead "teste 501" (criado anteriormente)
- ✅ Qualquer novo lead criado

---

**Versão**: v976  
**Data**: 2026-03-12  
**Commit**: 5538af06
