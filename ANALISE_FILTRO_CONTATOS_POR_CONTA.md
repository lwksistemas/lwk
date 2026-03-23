# Análise: Filtrar Contatos por Conta ao Criar Oportunidade

**Data**: 23/03/2026  
**Loja de Teste**: 41449198000172 (FELIX REPRESENTACOES E COMERCIO LTDA)  
**URL Problema**: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers

---

## Problema Relatado

Ao visualizar os detalhes de uma conta e clicar em "Criar Oportunidade", o sistema redireciona para a página de contatos, mas mostra TODOS os contatos do CRM, não apenas os contatos vinculados àquela conta específica.

**Comportamento Atual:**
1. Usuário acessa detalhes da conta "LLWK SISTEMAS"
2. Clica em "Criar Oportunidade"
3. Sistema redireciona para `/loja/{slug}/crm-vendas/contatos`
4. Mostra TODOS os contatos, não apenas os da conta "LLWK SISTEMAS"

**Comportamento Esperado:**
- Mostrar apenas os contatos vinculados à conta "LLWK SISTEMAS"
- Facilitar a seleção do contato correto ao criar a oportunidade

---

## Análise Técnica

### Backend ✅ JÁ IMPLEMENTADO

O `ContatoViewSet` já possui filtro por `conta_id`:

```python
def get_queryset(self):
    qs = super().get_queryset()
    # Filtros adicionais (além do filtro de vendedor do mixin)
    conta_id = self.request.query_params.get('conta_id')
    if conta_id:
        qs = qs.filter(conta_id=conta_id)
    return qs
```

**Endpoint:** `GET /crm-vendas/contatos/?conta_id={id}`

### Frontend ❌ NÃO IMPLEMENTADO

**Arquivo:** `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`

Função `handleCriarOportunidade()` (linha 308):
- Busca contatos da conta: `apiClient.get(\`/crm-vendas/contatos/?conta_id=${selectedConta.id}\`)`
- Valida se existe pelo menos um contato
- Cria lead automaticamente
- Redireciona para pipeline

**Problema:** Não redireciona para a página de contatos com filtro

---

## Solução Proposta

### Opção 1: Redirecionar para Contatos com Filtro (RECOMENDADA)

Quando o usuário clica em "Criar Oportunidade" e a conta não tem contatos:

```typescript
router.push(`/loja/${slug}/crm-vendas/contatos?criar=1&conta_id=${selectedConta.id}`);
```

Modificar `frontend/app/(dashboard)/loja/[slug]/crm-vendas/contatos/page.tsx`:
- Detectar `conta_id` na URL
- Filtrar contatos por conta
- Pré-selecionar a conta no formulário de criar contato

### Opção 2: Modal de Seleção de Contato

Criar modal na própria página de detalhes da conta:
- Listar contatos da conta
- Permitir selecionar contato
- Criar oportunidade com contato selecionado

---

## Implementação Escolhida: Opção 1

### Modificações Necessárias

1. **Página de Contatos** (`contatos/page.tsx`)
   - Adicionar filtro por `conta_id` da URL
   - Pré-selecionar conta ao criar novo contato
   - Mostrar mensagem indicando filtro ativo

2. **Página de Customers** (`customers/page.tsx`)
   - Já está correto (redireciona com `conta_id`)

---

## Arquivos a Modificar

1. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/contatos/page.tsx`
   - Adicionar leitura de `conta_id` da URL
   - Filtrar contatos por conta
   - Pré-selecionar conta no formulário

---

## Testes Necessários

1. Acessar detalhes de uma conta SEM contatos
2. Clicar em "Criar Oportunidade"
3. Verificar se redireciona para contatos com filtro
4. Verificar se mostra apenas contatos daquela conta
5. Criar novo contato e verificar se conta está pré-selecionada
6. Verificar se após criar contato, pode criar oportunidade

---

## Observações

- Backend já está preparado para filtrar por `conta_id`
- Solução é apenas no frontend
- Não requer deploy do backend
- Melhora UX ao criar oportunidades
