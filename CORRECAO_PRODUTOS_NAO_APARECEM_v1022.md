# Correção: Produtos/Serviços Não Aparecem na Lista (v1022)

**Data**: 18/03/2026  
**Versão**: v1022  
**Status**: ✅ CORRIGIDO

---

## 🔴 PROBLEMA

Após salvar um produto/serviço em `https://lwksistemas.com.br/loja/22239255889/crm-vendas/produtos-servicos`, ele não aparecia na lista.

### Comportamento Observado

1. ✅ Produto/serviço era salvo com sucesso (sem erro)
2. ❌ Produto/serviço NÃO aparecia na lista após salvar
3. ❌ Lista permanecia vazia mesmo após recarregar a página

---

## 🔍 ANÁLISE DA CAUSA RAIZ

### Problema no `get_queryset()`

O `ProdutoServicoViewSet` estava herdando o `get_queryset()` do `BaseModelViewSet`, que:

1. ✅ Valida que `loja_id` existe no contexto
2. ❌ **NÃO aplica filtro por `loja_id`** no queryset

```python
# BaseModelViewSet.get_queryset() - PROBLEMA
def get_queryset(self):
    queryset = self.queryset  # ❌ Usa queryset de classe sem filtro de loja
    
    if hasattr(self.queryset.model, 'loja_id'):
        loja_id = get_current_loja_id()
        if not loja_id:
            return queryset.none()
    
    # ❌ NÃO FILTRA POR loja_id!
    return queryset
```

### Por Que Aconteceu?

1. `ProdutoServico.objects.all()` retorna TODOS os produtos de TODAS as lojas
2. `BaseModelViewSet` apenas valida contexto, mas não filtra
3. `LojaIsolationManager` deveria filtrar automaticamente, mas não funciona com `self.queryset` (atributo de classe)

---

## ✅ SOLUÇÃO IMPLEMENTADA

### Modificação no `ProdutoServicoViewSet`

Sobrescrever `get_queryset()` para aplicar filtro de loja explicitamente:

```python
def get_queryset(self):
    """Filtra produtos/serviços por loja_id e aplica filtros adicionais."""
    from tenants.middleware import get_current_loja_id
    loja_id = get_current_loja_id()
    
    if not loja_id:
        logger.warning(f"[ProdutoServicoViewSet] Acesso sem loja_id no contexto")
        return ProdutoServico.objects.none()
    
    # ✅ Filtrar por loja_id explicitamente
    qs = ProdutoServico.objects.filter(loja_id=loja_id)
    
    # Filtros adicionais
    ativo = self.request.query_params.get('ativo')
    if ativo is not None:
        qs = qs.filter(ativo=ativo.lower() == 'true')
    tipo = self.request.query_params.get('tipo')
    if tipo:
        qs = qs.filter(tipo=tipo)
    return qs
```

---

## 📋 ARQUIVOS MODIFICADOS

### Backend

- `backend/crm_vendas/views.py`
  - Modificado `ProdutoServicoViewSet.get_queryset()` para filtrar por `loja_id` explicitamente

---

## 🚀 DEPLOY

### Backend (Heroku)

```bash
cd /caminho/do/projeto
git add backend/crm_vendas/views.py
git commit -m "fix(crm): corrige filtro de produtos/serviços por loja_id (v1022)"
git push heroku master
```

**Versão esperada**: v1126

---

## ✅ RESULTADO ESPERADO

1. ✅ Produtos/serviços aparecem na lista imediatamente após salvar
2. ✅ Lista mostra apenas produtos/serviços da loja atual
3. ✅ Filtros por tipo (produto/serviço) e status (ativo/inativo) funcionam corretamente

---

## 🔄 IMPACTO EM OUTROS VIEWSETS

### Verificar Outros ViewSets

Outros ViewSets que herdam de `BaseModelViewSet` podem ter o mesmo problema:

- ✅ `VendedorViewSet` - Tem `get_queryset()` próprio
- ✅ `ContaViewSet` - Usa `VendedorFilterMixin` que filtra por loja
- ✅ `LeadViewSet` - Tem `get_queryset()` próprio
- ✅ `ContatoViewSet` - Tem `get_queryset()` próprio
- ✅ `OportunidadeViewSet` - Tem `get_queryset()` próprio
- ✅ `AtividadeViewSet` - Tem `get_queryset()` próprio
- ❓ `OportunidadeItemViewSet` - Verificar se precisa de correção
- ❓ `PropostaViewSet` - Verificar se precisa de correção
- ❓ `ContratoViewSet` - Verificar se precisa de correção

---

## 📝 LIÇÕES APRENDIDAS

1. **Sempre filtrar por `loja_id` explicitamente** em ViewSets multi-tenant
2. **Não confiar apenas em `LojaIsolationManager`** com `self.queryset` de classe
3. **Testar criação E listagem** após implementar CRUD
4. **`BaseModelViewSet` precisa ser corrigido** para aplicar filtro de loja automaticamente

---

## 🔗 REFERÊNCIAS

- Correção anterior: `CORRECAO_PERMISSOES_OWNER_v1020.md`
- Sistema de migrations: `CORRECAO_DEFINITIVA_v1016.md`
- Vinculação admin-vendedor: `ANALISE_ADMIN_NAO_VINCULADO_VENDEDOR.md`
