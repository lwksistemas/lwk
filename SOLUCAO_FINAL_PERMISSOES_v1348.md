# Solução Final - Problema de Permissões Intermitentes CRM Vendas
**Versão: v1348**
**Data: 2026-03-26**

## 🎯 PROBLEMA RESOLVIDO

Após login, administrador (owner) tinha acesso completo às configurações do CRM Vendas, mas após alguns minutos o sistema bloqueava o acesso, mostrando apenas 1 opção ao invés de todas.

## 🔍 CAUSA RAIZ IDENTIFICADA

O problema estava em **3 locais** do frontend que chamavam `authService.setVendedorId()`:

1. **`frontend/lib/auth.ts`** (linha 282): Função `setVendedorId()` estava setando `is_vendedor=1` quando owner tinha `vendedor_id`
2. **`frontend/app/(dashboard)/loja/[slug]/crm-vendas/layout.tsx`** (linha 67): Layout estava setando `is_vendedor=1` ao sincronizar `vendedor_id`
3. **`frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`** (linhas 81 e 232): Pipeline chamava `setVendedorId()` sem verificar se era owner

### Por que isso causava o problema?

- Owner tem `vendedor_id` (criado pelo signal para permitir fazer vendas)
- Código frontend estava interpretando "tem vendedor_id" = "é vendedor"
- Quando setava `is_vendedor=1`, o sistema bloqueava acesso administrativo
- Isso acontecia após alguns minutos porque:
  - Login inicial não setava `is_vendedor=1` (correto)
  - Mas ao navegar para Pipeline ou ao layout sincronizar, chamava `setVendedorId()`
  - `setVendedorId()` setava `is_vendedor=1` (incorreto para owner)
  - Sistema bloqueava acesso

## ✅ CORREÇÕES IMPLEMENTADAS

### 1. `frontend/lib/auth.ts` - Função `setVendedorId()`

```typescript
setVendedorId(vendedorId: number): void {
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('current_vendedor_id', String(vendedorId));
    // Só marca como vendedor se NÃO for owner
    // Owner já tem is_vendedor !== '1' do login
    const isAlreadyVendedor = sessionStorage.getItem('is_vendedor') === '1';
    if (isAlreadyVendedor) {
      // Já é vendedor, mantém
      sessionStorage.setItem('is_vendedor', '1');
    }
    // Se não é vendedor (owner), NÃO seta is_vendedor
  }
}
```

**Lógica**: Só seta `is_vendedor=1` se JÁ for vendedor. Owner nunca terá `is_vendedor=1`.

### 2. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/layout.tsx`

```typescript
const fetchCrmMe = useCallback(async () => {
  try {
    const r = await apiClient.get<{
      vendedor_id: number | null;
      is_vendedor: boolean;
      user_display_name?: string | null;
      user_role?: 'vendedor' | 'administrador';
    }>('/crm-vendas/me/');
    const d = r.data;
    // IMPORTANTE: Só setar is_vendedor se o BACKEND explicitamente disser que é vendedor
    // Owner pode ter vendedor_id mas is_vendedor=false (acesso total)
    if (typeof window !== 'undefined') {
      if (d?.is_vendedor === true && typeof d?.vendedor_id === 'number') {
        sessionStorage.setItem('is_vendedor', '1');
        sessionStorage.setItem('current_vendedor_id', String(d.vendedor_id));
      } else if (typeof d?.vendedor_id === 'number') {
        // Tem vendedor_id mas não é vendedor (owner) - só salva o ID
        sessionStorage.setItem('current_vendedor_id', String(d.vendedor_id));
        // NÃO seta is_vendedor - owner mantém acesso total
      }
    }
    // ...
  } catch {
    /* ignore */
  }
}, []);
```

**Lógica**: Só seta `is_vendedor=1` se backend explicitamente retornar `is_vendedor=true`.

### 3. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`

**Correção 1 - useEffect inicial (linha 77-89)**:
```typescript
useEffect(() => {
  apiClient
    .get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/')
    .then((res) => {
      const { vendedor_id, is_vendedor } = res.data;
      // Só sincronizar vendedor_id se o backend explicitamente disser que é vendedor
      // Owner pode ter vendedor_id mas não deve ser marcado como vendedor
      if (vendedor_id && is_vendedor === true) {
        authService.setVendedorId(vendedor_id);
      } else if (vendedor_id) {
        // Owner tem vendedor_id mas não é vendedor - só salva o ID sem marcar como vendedor
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('current_vendedor_id', String(vendedor_id));
        }
      }
      setVendedorIdSynced(true);
    })
    .catch(() => {
      setVendedorIdSynced(true);
    });
}, []);
```

**Correção 2 - Após criar oportunidade (linha 228-243)**:
```typescript
// Sincronizar vendedor_id antes de recarregar lista
try {
  const meRes = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
  const { vendedor_id, is_vendedor } = meRes.data;
  // Só sincronizar se for vendedor explicitamente
  if (vendedor_id && is_vendedor === true) {
    authService.setVendedorId(vendedor_id);
  } else if (vendedor_id) {
    // Owner - só salva o ID
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('current_vendedor_id', String(vendedor_id));
    }
  }
} catch {
  // Ignora erro de sincronização
}
```

**Lógica**: Verifica `is_vendedor` do backend antes de chamar `setVendedorId()`. Owner só salva o ID.

## 🚀 DEPLOY

```bash
# Frontend
cd frontend
git add -A
git commit -m "fix: corrigir problema de permissões intermitentes no CRM Vendas - v1348"
vercel --prod
```

**Deploy concluído**: https://lwksistemas.com.br

## 🧪 TESTE

1. Acessar: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes
2. Login como owner (Felix Representações)
3. Verificar que todas as opções aparecem
4. Navegar para Pipeline e voltar para Configurações
5. Aguardar alguns minutos
6. Verificar que todas as opções continuam aparecendo (problema resolvido)

## 📊 LOJAS AFETADAS (CORRIGIDAS)

1. **Felix Representações** (41449198000172) ✅
2. **ULTRASIS INFORMATICA LTDA** (38900437000154) ✅
3. **US MEDICAL** (18275574000138) ✅

## 🔑 CONCEITOS IMPORTANTES

### Owner vs Vendedor

- **Owner (Administrador)**:
  - `is_vendedor != 1` (ou não existe)
  - Tem `vendedor_id` (para fazer vendas)
  - Acesso TOTAL ao CRM (todas as configurações)
  - Backend retorna `is_vendedor=false` ou não retorna

- **Vendedor (Funcionário)**:
  - `is_vendedor = 1`
  - Tem `vendedor_id`
  - Acesso LIMITADO (só vendas, sem configurações)
  - Backend retorna `is_vendedor=true`

### Regra de Ouro

**NUNCA setar `is_vendedor=1` para owner, mesmo que tenha `vendedor_id`!**

## 📝 ARQUIVOS MODIFICADOS

1. `frontend/lib/auth.ts` - Função `setVendedorId()` corrigida
2. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/layout.tsx` - Sincronização corrigida
3. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx` - 2 chamadas corrigidas

## ✅ STATUS FINAL

- ✅ Backend: Signal corrigido (v1347 - deployed)
- ✅ Frontend: Permissões corrigidas (v1348 - deployed)
- ✅ 3 lojas com vendedor admin criado (Vendedor + VendedorUsuario)
- ✅ Problema de permissões intermitentes RESOLVIDO
- ✅ Administrador aparece na lista de funcionários

## 🎉 RESULTADO

Owner agora:
- Mantém acesso total permanentemente (sem bloqueios intermitentes)
- Aparece na lista de funcionários como "Administrador"
- Pode fazer vendas (tem vendedor_id) mas mantém acesso administrativo completo
