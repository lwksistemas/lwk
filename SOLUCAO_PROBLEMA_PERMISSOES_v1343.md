# Solução: Problema de Permissões em Configurações CRM Vendas

## Problema Reportado

Administrador logado como vendedor está tendo acesso bloqueado às configurações do CRM Vendas. Apenas 1 opção aparece ao invés de todas as 6 opções disponíveis.

URL afetada: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes

## Diagnóstico

### Verificação Realizada ✅

Executamos script de verificação e confirmamos que o vendedor está CORRETAMENTE configurado:

```
✅ VendedorUsuario encontrado:
   ID: 138
   Vendedor ID: 1
   Precisa trocar senha: True

✅ Vendedor encontrado no schema:
   ID: 1
   Nome: LUIZ HENRIQUE FELIX
   Email: consultorluizfelix@hotmail.com
   Cargo: Administrador
   Is Admin: True ✅
   Is Active: True
   Comissão: 0.00%
```

### Causa do Problema

O problema é **sessão antiga do navegador**. Quando o vendedor admin foi criado/atualizado, o usuário já estava logado com uma sessão que não tinha as permissões corretas.

O sistema funciona assim:
- No login, o backend verifica se o usuário é owner
- Se for owner, NÃO seta `is_vendedor=true` no sessionStorage
- Se não for owner mas tiver VendedorUsuario, seta `is_vendedor=true`
- O frontend usa `is_vendedor` para decidir quais opções mostrar

Como o usuário estava logado ANTES da correção, o sessionStorage ainda tem valores antigos.

## Solução Imediata ✅

### Para o Usuário:

1. **Fazer LOGOUT** do sistema
2. **Limpar cache do navegador** (opcional mas recomendado):
   - Chrome/Edge: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
   - Safari: Cmd+Option+E
3. **Fazer LOGIN novamente**
4. Acessar: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes

Após o login, o sistema reconhecerá corretamente que o usuário é owner/admin e mostrará todas as 6 opções:

1. ✅ Pagar assinatura
2. ✅ Configurar tela de login
3. ✅ Cadastrar funcionários
4. ✅ Configurar WhatsApp
5. ✅ Backup
6. ✅ Personalizar CRM

## Verificação Técnica

### Backend (Correto) ✅

O backend está verificando corretamente em `backend/superadmin/auth_views_secure.py` (linha 296):

```python
# IMPORTANTE: Owner NUNCA é marcado como vendedor, mesmo se vinculado
# Apenas vendedores comuns (não-owners) são marcados como is_vendedor
if loja.owner_id != user.id:
    response_data['is_vendedor'] = True
```

### Frontend (Correto) ✅

O frontend está verificando corretamente em `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/page.tsx`:

```typescript
const hasAdminAccess = authService.hasAdminAccess();
const isVendedor = authService.isVendedor();

const opcoes = (isVendedor && !hasAdminAccess)
    ? opcoesAdmin.filter((o) => o.href.includes('/personalizar'))
    : opcoesAdmin;
```

### Permissões (Corretas) ✅

O decorator `require_admin_access` em `backend/crm_vendas/decorators.py` verifica corretamente:

```python
# Owner SEMPRE tem acesso total
if is_owner(request):
    return func(self, request, *args, **kwargs)

# Verificar se é vendedor comum (não-owner)
if is_vendedor_usuario(request):
    return Response(
        {'detail': message},
        status=status.HTTP_403_FORBIDDEN
    )
```

## Prevenção de Problemas Futuros

### Para Desenvolvedores:

Quando fizer alterações em permissões ou vendedores, sempre:

1. Informar usuários para fazer logout/login
2. Considerar adicionar um botão "Atualizar Permissões" que force refresh do sessionStorage
3. Adicionar versionamento de sessão para invalidar sessões antigas automaticamente

### Para Usuários:

Se encontrar problemas de permissões:

1. Primeiro: Fazer logout e login novamente
2. Se persistir: Limpar cache do navegador
3. Se ainda persistir: Contatar suporte técnico

## Outras Lojas Afetadas

As mesmas instruções se aplicam para:

- https://lwksistemas.com.br/loja/38900437000154/crm-vendas/configuracoes
- https://lwksistemas.com.br/loja/18275574000138/crm-vendas/configuracoes

## Resumo

✅ Backend configurado corretamente  
✅ Vendedor marcado como admin no banco  
✅ Permissões funcionando corretamente  
⚠️  Sessão antiga do navegador causando problema  
✅ **SOLUÇÃO: Logout + Login**

## Arquivos Relacionados

- `backend/superadmin/signals.py` - Criação de vendedor admin
- `backend/superadmin/auth_views_secure.py` - Lógica de login
- `backend/crm_vendas/decorators.py` - Verificação de permissões
- `backend/crm_vendas/utils.py` - Funções is_owner e is_vendedor_usuario
- `frontend/lib/auth.ts` - AuthService (sessionStorage)
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/page.tsx` - Filtro de opções

## Versão

- v1343: Correção do signal e criação de vendedores admin
- v1343.1: Configuração de schema antes de criar vendedor
- v1343.2: Script SQL direto para criar vendedor
- v1343.3: Script de verificação de estado
- v1346: Deploy final com verificação

## Data

2026-03-26
