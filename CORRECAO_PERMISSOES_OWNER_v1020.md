# Correção: Owner com Acesso Total Mesmo Vinculado como Vendedor (v1020)

**Data**: 18/03/2026  
**Versão Heroku**: v1122  
**Status**: ✅ CORRIGIDO

---

## 🐛 Problema Identificado

Após vincular o administrador (owner) como vendedor na v1019, ele **perdeu acesso às configurações** do CRM.

### Sintomas
- Owner só via 1 opção em: `https://lwksistemas.com.br/loja/22239255889/crm-vendas/configuracoes`
- Deveria ver todas as opções (Funcionários, WhatsApp, Login, etc.)
- Owner estava sendo tratado como vendedor comum

### Causa Raiz
O decorator `require_admin_access` e o mixin `CRMPermissionMixin` bloqueavam qualquer usuário com `VendedorUsuario`, incluindo o owner.

**Código problemático**:
```python
def require_admin_access():
    def wrapper(self, request, *args, **kwargs):
        if is_vendedor_usuario(request):  # ❌ Bloqueava owner também
            return Response({'detail': 'Sem permissão'}, status=403)
        return func(self, request, *args, **kwargs)
```

**Resultado**: Owner vinculado como vendedor = bloqueado das configurações

---

## ✅ Solução Implementada

### 1. Modificado `require_admin_access` (decorators.py)

```python
def require_admin_access(message='...'):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # ✅ NOVO: Verificar se é owner ANTES de bloquear
            loja_id = get_current_loja_id()
            if loja_id:
                from superadmin.models import Loja
                loja = Loja.objects.using('default').filter(id=loja_id).first()
                if loja and loja.owner_id == request.user.id:
                    # Owner SEMPRE tem acesso total
                    return func(self, request, *args, **kwargs)
            
            # Verificar se é vendedor comum (não-owner)
            if is_vendedor_usuario(request):
                return Response({'detail': message}, status=403)
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
```

### 2. Modificado `CRMPermissionMixin.bloquear_vendedor` (mixins.py)

```python
def bloquear_vendedor(self, request, mensagem=None):
    """
    Retorna Response 403 se vendedor comum.
    Owner SEMPRE tem acesso total.
    """
    from tenants.middleware import get_current_loja_id
    from superadmin.models import Loja
    
    # ✅ NOVO: Verificar se é owner ANTES de bloquear
    loja_id = get_current_loja_id()
    if loja_id:
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            # Owner SEMPRE tem acesso total
            return None
    
    # Verificar se é vendedor comum (não-owner)
    if is_vendedor_usuario(request):
        msg = mensagem or 'Vendedores não têm permissão...'
        return Response({'detail': msg}, status=403)
    
    return None
```

---

## 🎯 Resultado

### Antes da Correção (v1019-v1121)
- ❌ Owner vinculado como vendedor: Acesso BLOQUEADO às configurações
- ❌ Owner só via 1 opção no menu de configurações
- ✅ Owner podia fazer vendas (tinha vendedor_id)

### Depois da Correção (v1122)
- ✅ Owner vinculado como vendedor: Acesso TOTAL às configurações
- ✅ Owner vê TODAS as opções no menu de configurações
- ✅ Owner pode fazer vendas (tem vendedor_id)
- ✅ Vendedores comuns continuam bloqueados (segurança mantida)

---

## 🔐 Regras de Permissão (Definitivas)

### Owner (Proprietário da Loja)
- ✅ Acesso TOTAL às configurações
- ✅ Pode criar/editar/excluir funcionários
- ✅ Pode fazer vendas (se vinculado como vendedor)
- ✅ Vê TODOS os dados da loja
- ✅ Nunca é bloqueado por `require_admin_access`

### Vendedor Comum (VendedorUsuario não-owner)
- ❌ SEM acesso às configurações
- ❌ NÃO pode criar/editar/excluir funcionários
- ✅ Pode fazer vendas
- ✅ Vê apenas seus próprios dados
- ❌ Bloqueado por `require_admin_access`

---

## 📝 Arquivos Modificados

1. `backend/crm_vendas/decorators.py`
   - Modificado `require_admin_access()` para verificar owner primeiro

2. `backend/crm_vendas/mixins.py`
   - Modificado `CRMPermissionMixin.bloquear_vendedor()` para verificar owner primeiro

---

## 🧪 Como Testar

### 1. Acessar Configurações como Owner
```
URL: https://lwksistemas.com.br/loja/22239255889/crm-vendas/configuracoes
Login: financeiroluiz@hotmail.com

✅ Deve ver TODAS as opções:
- Funcionários
- WhatsApp
- Personalização de Login
- Origens de Leads
- Etapas do Funil
- Produtos e Serviços
```

### 2. Criar Lead como Owner
```
URL: https://lwksistemas.com.br/loja/22239255889/crm-vendas/leads
Login: financeiroluiz@hotmail.com

✅ Lead deve ficar vinculado ao vendedor (Daniel Souza Felix)
✅ Lead deve aparecer no dashboard
```

### 3. Verificar Vendedor Comum (se houver)
```
Login: [email do vendedor]

❌ NÃO deve ver opção "Configurações"
✅ Deve ver apenas seus próprios leads/oportunidades
```

---

## 📊 Commits

1. **v1019** (413f46ba): Implementação inicial - vincular owner como vendedor
2. **v1020** (51358f72): Correção de permissões - owner tem acesso total

---

## 🎉 Conclusão

Problema resolvido! Owner agora tem:
- ✅ Acesso total às configurações (como administrador)
- ✅ Capacidade de fazer vendas (como vendedor)
- ✅ Visão completa de todos os dados da loja

**Versão em produção**: v1122  
**Testado em**: https://lwksistemas.com.br/loja/22239255889/crm-vendas/configuracoes
