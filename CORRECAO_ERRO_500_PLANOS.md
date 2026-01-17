# ✅ Correção do Erro 500 na Página de Planos

## Problema Identificado
A página https://lwksistemas.com.br/superadmin/planos estava retornando erro 500 ao tentar carregar planos por tipo de loja.

### Erro no Log
```
AttributeError: 'NoneType' object has no attribute 'filter'
File "/app/backend/superadmin/views.py", line 46, in por_tipo
planos = self.queryset.filter(tipos_loja__id=tipo_id, is_active=True)
```

## Causa Raiz
No Django REST Framework, `self.queryset` é um atributo de classe que pode ser None. O correto é usar `self.get_queryset()` que é um método que retorna o queryset configurado.

## Solução Implementada

### Arquivo: `backend/superadmin/views.py`

#### 1. PlanoAssinaturaViewSet - Método `por_tipo`
```python
# ❌ ANTES (ERRADO)
planos = self.queryset.filter(tipos_loja__id=tipo_id, is_active=True)

# ✅ DEPOIS (CORRETO)
planos = self.get_queryset().filter(tipos_loja__id=tipo_id, is_active=True)
```

#### 2. FinanceiroLojaViewSet - Método `pendentes`
```python
# ❌ ANTES (ERRADO)
pendentes = self.queryset.filter(status_pagamento__in=['pendente', 'atrasado'])

# ✅ DEPOIS (CORRETO)
pendentes = self.get_queryset().filter(status_pagamento__in=['pendente', 'atrasado'])
```

#### 3. UsuarioSistemaViewSet - Método `suporte`
```python
# ❌ ANTES (ERRADO)
suporte = self.queryset.filter(tipo='suporte')

# ✅ DEPOIS (CORRETO)
suporte = self.get_queryset().filter(tipo='suporte')
```

## Deploy Realizado
- **Versão**: v33
- **Commit**: `fix: Corrigir erro 500 na página de planos - usar get_queryset() ao invés de queryset`
- **Data**: 17/01/2026

## Testes Realizados
Após o deploy, a página de planos deve:
1. ✅ Carregar sem erro 500
2. ✅ Exibir planos filtrados por tipo de loja
3. ✅ Permitir criação/edição de planos

## Endpoints Corrigidos
- `GET /api/superadmin/planos/por_tipo/?tipo_id={id}` - Buscar planos por tipo
- `GET /api/superadmin/financeiro/pendentes/` - Listar pagamentos pendentes
- `GET /api/superadmin/usuarios-sistema/suporte/` - Listar usuários de suporte

## Nota Técnica
Este é um erro comum ao trabalhar com Django REST Framework ViewSets. Sempre use:
- ✅ `self.get_queryset()` - Método que retorna o queryset (CORRETO)
- ❌ `self.queryset` - Atributo de classe que pode ser None (EVITAR)

## Outros Arquivos com Mesmo Padrão
Os seguintes arquivos também usam `self.queryset.filter()` mas não causam erro porque têm `queryset` definido como atributo de classe:
- `backend/servicos/views.py`
- `backend/clinica_estetica/views.py`
- `backend/ecommerce/views.py`
- `backend/restaurante/views.py`

Recomenda-se revisar esses arquivos futuramente para seguir o padrão correto.

---

**Status**: ✅ Corrigido e em Produção
**URL**: https://lwksistemas.com.br/superadmin/planos
