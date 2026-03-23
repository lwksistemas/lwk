# Análise: Problema com Gerente de Vendas

**Data**: 23/03/2026  
**Loja**: 41449198000172 (FELIX REPRESENTACOES E COMERCIO LTDA)  
**Usuário Problema**: Felipe Felix (pjluiz25@hotmail.com)

---

## Problema Relatado

1. Gerente cadastrado não está liberado - sistema não aparece
2. Configurações mostram apenas 1 opção (deveria mostrar todas)
3. Home não mostra valores do dashboard
4. Pipeline mostra apenas 1 oportunidade (deveria mostrar todas)

---

## Análise Técnica

### Estrutura Atual

**Owner da Loja:**
- Email: consultorluizfelix@hotmail.com
- ID: 163
- Acesso: COMPLETO (owner)

**Gerente de Vendas:**
- Nome: Felipe Felix
- Email: pjluiz25@hotmail.com
- Grupo: Gerente de Vendas
- VendedorUsuario: SIM (vinculado)
- Acesso: RESTRITO (tratado como vendedor comum)

### Lógica Atual do Backend

```python
# backend/superadmin/auth_views_secure.py (linha 295-297)
# IMPORTANTE: Owner NUNCA é marcado como vendedor, mesmo se vinculado
# Apenas vendedores comuns (não-owners) são marcados como is_vendedor
if loja.owner_id != user.id:
    response_data['is_vendedor'] = True
```

**Problema:** Qualquer usuário que NÃO seja owner é marcado como `is_vendedor=True`, independente do grupo.

### Lógica Atual do Frontend

```typescript
// frontend/lib/auth.ts
isVendedor(): boolean {
  return sessionStorage.getItem('is_vendedor') === '1';
}

isOwner(): boolean {
  // Se não é vendedor, é owner (administrador)
  return sessionStorage.getItem('is_vendedor') !== '1';
}
```

**Problema:** Frontend usa `is_vendedor` para determinar permissões, mas não considera o grupo do usuário.

---

## Impactos

1. **Configurações**: Gerente vê apenas "Personalizar CRM" (lógica de vendedor)
2. **Dashboard**: Gerente vê apenas suas próprias oportunidades (filtro de vendedor)
3. **Pipeline**: Gerente vê apenas oportunidades onde é responsável
4. **Permissões**: Gerente não consegue acessar funcionalidades administrativas

---

## Solução Proposta

### Opção 1: Adicionar Flag `is_gerente` no Backend (RECOMENDADA)

Modificar `auth_views_secure.py` para adicionar flag `is_gerente`:

```python
if loja.owner_id != user.id:
    response_data['is_vendedor'] = True
    response_data['vendedor_id'] = vu.vendedor_id
    
    # Verificar se é Gerente de Vendas
    from django.contrib.auth.models import Group
    if user.groups.filter(name='Gerente de Vendas').exists():
        response_data['is_gerente'] = True
```

Modificar frontend para usar `is_gerente`:

```typescript
isGerente(): boolean {
  return sessionStorage.getItem('is_gerente') === '1';
}

// Usar em verificações de permissão
if (authService.isOwner() || authService.isGerente()) {
  // Acesso completo
}
```

### Opção 2: Não Marcar Gerente como Vendedor

Modificar backend para NÃO marcar gerentes como `is_vendedor`:

```python
if loja.owner_id != user.id:
    # Verificar se é Gerente de Vendas
    from django.contrib.auth.models import Group
    is_gerente = user.groups.filter(name='Gerente de Vendas').exists()
    
    if not is_gerente:
        response_data['is_vendedor'] = True
    
    response_data['vendedor_id'] = vu.vendedor_id
```

**Problema:** Gerente não seria associado a oportunidades como vendedor.

### Opção 3: Adicionar Permissões Específicas

Usar sistema de permissões do Django para verificar acesso:

```python
# Backend: verificar permissão ao invés de is_vendedor
if user.has_perm('crm_vendas.view_all_oportunidades'):
    # Mostrar todas as oportunidades
```

**Problema:** Mais complexo, requer mudanças em muitos lugares.

---

## Implementação Escolhida: Opção 1

Adicionar flag `is_gerente` que indica se o usuário pertence ao grupo "Gerente de Vendas".

### Vantagens
- Simples de implementar
- Não quebra lógica existente
- Gerente continua sendo vendedor (pode ter oportunidades)
- Gerente tem acesso completo como owner

### Modificações Necessárias

1. **Backend** (`auth_views_secure.py`)
   - Adicionar `is_gerente` na resposta do login
   - Verificar se usuário pertence ao grupo "Gerente de Vendas"

2. **Frontend** (`lib/auth.ts`)
   - Adicionar método `isGerente()`
   - Salvar `is_gerente` no sessionStorage

3. **Frontend** (componentes)
   - Modificar verificações de permissão para incluir `isGerente()`
   - Páginas de configuração
   - Dashboard
   - Pipeline (filtros)

---

## Arquivos a Modificar

1. `backend/superadmin/auth_views_secure.py` - Adicionar is_gerente
2. `frontend/lib/auth.ts` - Adicionar método isGerente()
3. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/page.tsx` - Usar isGerente()
4. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/page.tsx` - Dashboard sem filtro para gerente
5. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx` - Mostrar todas oportunidades

---

## Testes Necessários

1. Login como Gerente de Vendas (Felipe Felix)
2. Verificar se `is_gerente=true` no sessionStorage
3. Acessar configurações e verificar todas as opções
4. Verificar dashboard com todos os valores
5. Verificar pipeline com todas as oportunidades
6. Criar oportunidade e verificar se gerente é associado
7. Login como vendedor comum e verificar restrições

---

## Observações

- Gerente de Vendas deve ter acesso COMPLETO como owner
- Gerente de Vendas continua sendo vendedor (pode ter oportunidades)
- Vendedor comum continua com acesso restrito
- Owner continua com acesso completo
