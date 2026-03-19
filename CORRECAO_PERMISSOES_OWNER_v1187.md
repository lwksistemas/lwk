# Correção de Permissões do Owner - v1187

## Problema
Owner da loja está sendo tratado como vendedor, tendo acesso limitado às configurações.

## Causa Raiz
O owner tem um registro `VendedorUsuario` vinculado, o que faz o sistema marcar `is_vendedor=true` no sessionStorage, mesmo que o backend esteja retornando corretamente `is_vendedor=false`.

## Solução Temporária (Teste)
Executar no console do navegador:
```javascript
sessionStorage.removeItem('is_vendedor');
sessionStorage.removeItem('current_vendedor_id');
location.reload();
```

## Solução Definitiva

### 1. Garantir que o backend NUNCA retorna is_vendedor para owner
O código em `backend/superadmin/auth_views_secure.py` linha 296 já está correto:
```python
if loja.owner_id != user.id:
    response_data['is_vendedor'] = True
```

### 2. Limpar sessionStorage no logout
Arquivo: `frontend/lib/auth.ts` linha 155
- ✅ Já limpa `is_vendedor` e `current_vendedor_id`

### 3. Garantir que o frontend respeita a resposta do backend
Arquivo: `frontend/lib/auth.ts` linhas 95-103

PROBLEMA: O código seta `is_vendedor` baseado na resposta, mas pode estar pegando de um login antigo.

Solução: Sempre limpar antes de setar:
```typescript
// Limpar flags de vendedor ANTES de processar novo login
sessionStorage.removeItem('is_vendedor');
sessionStorage.removeItem('current_vendedor_id');

// Só setar se vier explicitamente do backend
if ((data as any).is_vendedor === true) {
  sessionStorage.setItem('is_vendedor', '1');
  if (typeof (data as any).vendedor_id === 'number') {
    sessionStorage.setItem('current_vendedor_id', String((data as any).vendedor_id));
  }
}
```

### 4. Adicionar endpoint /api/crm-vendas/me/ para sincronizar
O endpoint já existe e retorna corretamente:
```json
{
  "vendedor_id": 123,
  "is_vendedor": false,  // FALSE para owner
  "user_display_name": "Luiz Henrique Felix",
  "user_role": "administrador"
}
```

Solução: Chamar este endpoint após login para garantir sincronização.

## Código Duplicado a Remover

### 1. Verificação de owner duplicada
Arquivos com verificação `loja.owner_id == request.user.id`:
- `backend/crm_vendas/utils.py` linha 122 (is_vendedor_usuario)
- `backend/crm_vendas/decorators.py` linha 130 (require_admin_access)
- `backend/crm_vendas/mixins.py` linha 48 (bloquear_vendedor)
- `backend/crm_vendas/mixins.py` linha 95 (filter_by_vendedor)
- `backend/crm_vendas/views.py` linha 1139 (crm_me)

SOLUÇÃO: Criar função helper única:
```python
# backend/crm_vendas/utils.py
def is_owner(request):
    """Verifica se o usuário é o proprietário da loja."""
    if not request or not request.user or not request.user.is_authenticated:
        return False
    loja_id = get_current_loja_id()
    if not loja_id:
        return False
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        return loja and loja.owner_id == request.user.id
    except Exception:
        return False
```

Depois usar em todos os lugares:
```python
from .utils import is_owner

if is_owner(request):
    return False  # Owner não é vendedor
```

### 2. Busca de loja duplicada
Múltiplos lugares fazem:
```python
loja = Loja.objects.using('default').filter(id=loja_id).first()
```

SOLUÇÃO: Usar a função existente `get_loja_from_context(request)`

### 3. Verificação de VendedorUsuario duplicada
Aparece em vários lugares:
```python
vu = VendedorUsuario.objects.using('default').filter(
    user=request.user,
    loja_id=loja_id,
).first()
```

SOLUÇÃO: Já existe `get_current_vendedor_id(request)` que faz isso.

## Implementação

### Passo 1: Criar função helper is_owner
```python
# backend/crm_vendas/utils.py
def is_owner(request):
    """
    Verifica se o usuário é o proprietário da loja.
    Owner SEMPRE tem acesso total, mesmo se tiver VendedorUsuario vinculado.
    """
    if not request or not request.user or not request.user.is_authenticated:
        return False
    loja_id = get_current_loja_id()
    if not loja_id:
        return False
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        return loja and loja.owner_id == request.user.id
    except Exception:
        return False
```

### Passo 2: Refatorar is_vendedor_usuario
```python
def is_vendedor_usuario(request):
    """
    Verifica se o usuário logado é um vendedor (VendedorUsuario), não o owner.
    Retorna True apenas se for um vendedor real, False para owner ou outros.
    """
    if not request or not request.user or not request.user.is_authenticated:
        return False
    
    # Owner NUNCA é vendedor
    if is_owner(request):
        return False
    
    # Verificar se tem vendedor_id (já faz a verificação de VendedorUsuario)
    return get_current_vendedor_id(request) is not None
```

### Passo 3: Refatorar decorators e mixins
Usar `is_owner(request)` em vez de buscar loja novamente.

### Passo 4: Corrigir frontend para limpar flags antes de setar
```typescript
// frontend/lib/auth.ts - método login()
// ANTES de salvar novos valores, limpar os antigos
sessionStorage.removeItem('is_vendedor');
sessionStorage.removeItem('current_vendedor_id');

// Só setar se vier do backend
if ((data as any).is_vendedor === true) {
  sessionStorage.setItem('is_vendedor', '1');
  // ...
}
```

### Passo 5: Adicionar sincronização após login
```typescript
// Após login bem-sucedido, sincronizar com /api/crm-vendas/me/
if (responseUserType === 'loja' && lojaSlug) {
  try {
    const meResponse = await apiClient.get('/api/crm-vendas/me/');
    if (meResponse.data.is_vendedor === false) {
      sessionStorage.removeItem('is_vendedor');
      sessionStorage.removeItem('current_vendedor_id');
    }
  } catch (e) {
    console.warn('Não foi possível sincronizar status de vendedor');
  }
}
```

## Testes
1. ✅ Owner sem VendedorUsuario → Acesso total
2. ✅ Owner com VendedorUsuario → Acesso total (não deve ser tratado como vendedor)
3. ✅ Vendedor comum → Acesso limitado
4. ✅ Logout/Login → Flags limpos corretamente

## Deploy
- Versão: v1187
- Arquivos modificados:
  - `backend/crm_vendas/utils.py`
  - `backend/crm_vendas/decorators.py`
  - `backend/crm_vendas/mixins.py`
  - `frontend/lib/auth.ts`
