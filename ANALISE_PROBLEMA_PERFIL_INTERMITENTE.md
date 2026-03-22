# Análise: Problema de Perfil Intermitente (Admin → Vendedor)

## Data: 22/03/2026

---

## 🚨 PROBLEMA RELATADO

**Sintoma:** Administrador (owner) está tendo seu perfil mudado intermitentemente para vendedor, perdendo acesso a configurações e relatórios.

**URL afetada:** https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes

**Impacto:** CRÍTICO - Owner perde acesso administrativo

---

## 🔍 INVESTIGAÇÃO

### 1. Lógica de Determinação de Perfil

**Backend (`backend/crm_vendas/utils.py`):**

```python
def is_owner(request):
    """Verifica se o usuário é o proprietário da loja."""
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    return loja and loja.owner_id == request.user.id

def is_vendedor_usuario(request):
    """Verifica se é vendedor (não-owner)."""
    # Owner NUNCA é vendedor
    if is_owner(request):
        return False
    # Verificar se tem vendedor_id
    return get_current_vendedor_id(request) is not None
```

**Endpoint `/crm-vendas/config/me/`:**

```python
# Owner NUNCA é marcado como vendedor
if vendedor_id is not None:
    if not is_owner:
        user_role = 'vendedor'
        is_vendedor = True

if is_owner and loja:
    user_role = 'administrador'
    is_vendedor = False
```

**Frontend (`frontend/lib/auth.ts`):**

```typescript
// Só setar is_vendedor se vier EXPLICITAMENTE como true
if ((data as any).is_vendedor === true) {
  sessionStorage.setItem('is_vendedor', '1');
}

isVendedor(): boolean {
  return sessionStorage.getItem('is_vendedor') === '1';
}
```

---

## 🐛 POSSÍVEIS CAUSAS

### Causa 1: Registro Duplicado de VendedorUsuario
- Owner pode ter sido cadastrado como vendedor por engano
- Sistema verifica `VendedorUsuario` antes de verificar se é owner
- **Solução:** Remover registro de VendedorUsuario do owner

### Causa 2: Cache do SessionStorage
- `is_vendedor` pode estar sendo mantido entre sessões
- Navegador pode estar restaurando sessionStorage antigo
- **Solução:** Limpar sessionStorage no login

### Causa 3: Race Condition
- Múltiplas chamadas simultâneas ao backend
- Uma retorna `is_vendedor=true` antes da outra
- **Solução:** Garantir ordem de execução

### Causa 4: Problema no Endpoint de Login
- Login pode estar setando `is_vendedor=true` incorretamente
- **Solução:** Verificar lógica do login

---

## ✅ VERIFICAÇÕES NECESSÁRIAS

### 1. Verificar Banco de Dados

```sql
-- Verificar se owner tem VendedorUsuario
SELECT 
    u.id as user_id,
    u.username,
    l.id as loja_id,
    l.nome as loja_nome,
    l.owner_id,
    vu.id as vendedor_usuario_id,
    vu.vendedor_id,
    v.nome as vendedor_nome
FROM auth_user u
JOIN superadmin_loja l ON l.owner_id = u.id
LEFT JOIN crm_vendas_vendedorusuario vu ON vu.user_id = u.id AND vu.loja_id = l.id
LEFT JOIN crm_vendas_vendedor v ON v.id = vu.vendedor_id
WHERE l.cpf_cnpj = '41449198000172';
```

### 2. Verificar SessionStorage

Abrir DevTools → Application → Session Storage:
- `is_vendedor` deve ser `null` ou não existir para owner
- `current_vendedor_id` deve ser `null` ou não existir para owner
- `user_type` deve ser `loja`

### 3. Verificar Response do Login

Abrir DevTools → Network → Filtrar por `login`:
- Response deve ter `is_vendedor: false` para owner
- Response deve ter `user_role: 'administrador'` para owner

---

## 🔧 SOLUÇÕES PROPOSTAS

### Solução 1: Remover VendedorUsuario do Owner (RECOMENDADO)

```python
# Script para limpar VendedorUsuario de owners
from superadmin.models import Loja, VendedorUsuario

loja = Loja.objects.get(cpf_cnpj='41449198000172')
owner = loja.owner

# Remover VendedorUsuario do owner se existir
VendedorUsuario.objects.filter(
    user=owner,
    loja=loja
).delete()

print(f"✅ VendedorUsuario removido para owner {owner.username}")
```

### Solução 2: Forçar Limpeza no Login

```typescript
// frontend/lib/auth.ts - Linha 86
// Limpar flags de vendedor ANTES de processar novo login
if (typeof window !== 'undefined') {
  sessionStorage.removeItem('is_vendedor');
  sessionStorage.removeItem('current_vendedor_id');
  sessionStorage.removeItem('user_role');  // ✅ ADICIONAR
}
```

### Solução 3: Adicionar Validação Extra no Backend

```python
# backend/superadmin/auth_views_secure.py
# Garantir que owner NUNCA seja marcado como vendedor
if loja and loja.owner_id == user.id:
    response_data['is_vendedor'] = False  # ✅ FORÇAR False
    response_data['user_role'] = 'administrador'
    # Remover vendedor_id se existir
    if 'vendedor_id' in response_data:
        del response_data['vendedor_id']
```

---

## 🚀 AÇÃO IMEDIATA

### Passo 1: Verificar Banco de Dados

Execute no Django shell:

```bash
heroku run python backend/manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja
from crm_vendas.models import VendedorUsuario

loja = Loja.objects.get(cpf_cnpj='41449198000172')
owner = loja.owner

print(f"Owner: {owner.username} (ID: {owner.id})")
print(f"Loja: {loja.nome} (ID: {loja.id})")
print(f"Owner ID da loja: {loja.owner_id}")

# Verificar se owner tem VendedorUsuario
vu = VendedorUsuario.objects.filter(user=owner, loja=loja).first()
if vu:
    print(f"❌ PROBLEMA: Owner tem VendedorUsuario (ID: {vu.id})")
    print(f"   Vendedor ID: {vu.vendedor_id}")
    print(f"   Vendedor Nome: {vu.vendedor.nome if vu.vendedor else 'N/A'}")
    print("\n🔧 SOLUÇÃO: Remover VendedorUsuario do owner")
    print("   VendedorUsuario.objects.filter(user=owner, loja=loja).delete()")
else:
    print("✅ OK: Owner NÃO tem VendedorUsuario")
```

### Passo 2: Limpar SessionStorage

No navegador (DevTools → Console):

```javascript
// Limpar tudo relacionado a vendedor
sessionStorage.removeItem('is_vendedor');
sessionStorage.removeItem('current_vendedor_id');
sessionStorage.removeItem('user_role');

// Fazer logout e login novamente
window.location.href = '/loja/41449198000172/login';
```

### Passo 3: Testar

1. Fazer login novamente
2. Verificar se tem acesso a configurações
3. Verificar se relatórios estão disponíveis
4. Monitorar por 24h para ver se problema volta

---

## 📊 LOGS PARA MONITORAMENTO

Adicionar logs temporários para debug:

```python
# backend/crm_vendas/utils.py - is_vendedor_usuario
def is_vendedor_usuario(request):
    if not request or not request.user or not request.user.is_authenticated:
        return False
    
    is_owner_result = is_owner(request)
    vendedor_id = get_current_vendedor_id(request)
    
    # ✅ LOG TEMPORÁRIO
    logger.warning(
        f"🔍 is_vendedor_usuario: user={request.user.username}, "
        f"is_owner={is_owner_result}, vendedor_id={vendedor_id}"
    )
    
    if is_owner_result:
        return False
    
    return vendedor_id is not None
```

---

## 📝 CONCLUSÃO

O problema mais provável é que o owner foi cadastrado como `VendedorUsuario` por engano, fazendo com que o sistema o identifique como vendedor em algumas situações.

**Próximos passos:**
1. Verificar banco de dados (Passo 1)
2. Se confirmado, remover VendedorUsuario do owner
3. Limpar sessionStorage
4. Testar e monitorar

---

**Status:** Aguardando verificação do banco de dados


---

## ✅ ATUALIZAÇÃO: PROBLEMA RESOLVIDO (22/03/2026)

### 🎯 CAUSA CONFIRMADA

O owner da loja foi cadastrado como `VendedorUsuario` por engano no banco de dados. Isso fazia com que o sistema o identificasse como vendedor em algumas situações, causando perda de acesso administrativo.

**Dados do problema:**
- Loja: FELIX REPRESENTACOES E COMERCIO LTDA (ID: 132, Slug: 41449198000172)
- Owner: felix (ID: 163, Email: consultorluizfelix@hotmail.com)
- VendedorUsuario ID: 104 (vinculado ao owner)
- Vendedor ID: 1

### ✅ CORREÇÃO APLICADA

Executado comando: `python manage.py fix_owner_vendedor 41449198000172 --confirm`

**Resultado:** 1 VendedorUsuario removido com sucesso.

### 📋 PRÓXIMOS PASSOS PARA O USUÁRIO

1. **Limpar sessionStorage do navegador:**
   - Abrir DevTools (F12)
   - Ir em Application → Session Storage → https://lwksistemas.com.br
   - Remover as seguintes chaves:
     - `is_vendedor`
     - `current_vendedor_id`
     - `user_role`
   
   **OU executar no Console do navegador:**
   ```javascript
   sessionStorage.removeItem('is_vendedor');
   sessionStorage.removeItem('current_vendedor_id');
   sessionStorage.removeItem('user_role');
   console.log('✅ SessionStorage limpo!');
   ```

2. **Fazer logout e login novamente:**
   - Acessar: https://lwksistemas.com.br/loja/41449198000172/login
   - Fazer login com suas credenciais

3. **Verificar acesso:**
   - Acessar: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes
   - Verificar se tem acesso a todas as opções de configuração
   - Verificar se tem acesso a relatórios

4. **Monitorar por 24h** para confirmar que o problema não volta

### 🔧 COMANDOS CRIADOS

Foram criados dois comandos Django para diagnosticar e corrigir este tipo de problema:

1. **Verificar problema:**
   ```bash
   python manage.py check_owner_vendedor <slug_loja>
   ```

2. **Corrigir problema:**
   ```bash
   python manage.py fix_owner_vendedor <slug_loja> --confirm
   ```

**Deploy:** Heroku v1240

### 🛡️ PREVENÇÃO FUTURA

Para evitar que este problema ocorra novamente, considerar adicionar validação no backend para impedir que owners sejam cadastrados como VendedorUsuario.

---

**Status Final:** ✅ RESOLVIDO - Aguardando confirmação do usuário
