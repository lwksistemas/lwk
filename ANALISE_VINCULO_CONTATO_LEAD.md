# Análise: Vínculo de Contato ao Lead

## Problema Identificado
Ao criar uma nova oportunidade a partir de uma conta, o sistema não estava vinculando o contato específico ao lead, apenas a conta. Isso causava confusão sobre qual pessoa de contato estava relacionada à oportunidade.

## Solução Implementada

### 1. Backend - Modelo Lead
**Arquivo**: `backend/crm_vendas/models.py`

Adicionado campo `contato` ao modelo Lead:
```python
contato = models.ForeignKey(
    'Contato',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='leads',
    help_text='Contato específico vinculado ao lead',
)
```

### 2. Backend - Migração
**Arquivo**: `backend/crm_vendas/migrations/0030_add_contato_to_lead.py`

- Criada migração para adicionar campo `contato` ao modelo Lead
- Adicionado índice composto `['loja_id', 'contato']` para otimização de queries
- Dependência corrigida para `0029_add_categoria_codigo_produto_servico`

### 3. Backend - Serializers
**Arquivo**: `backend/crm_vendas/serializers.py`

Atualizados serializers para incluir informações do contato:

**LeadSerializer**:
- Campo `contato` (write) para receber ID do contato
- Campo `contato_info` (read-only) com dados completos do contato:
  - id, nome, email, telefone, cargo

**LeadListSerializer**:
- Campo `contato_nome` para exibição rápida na listagem

### 4. Frontend - Criação de Oportunidade
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`

Função `handleCriarOportunidade` atualizada:

1. Busca contatos da conta selecionada
2. Valida se existe pelo menos um contato
3. Se não houver contatos, redireciona para cadastro
4. Usa dados do primeiro contato para criar o lead
5. Envia `contato_id` no payload do lead:

```typescript
const leadPayload = {
  nome: primeiroContato.nome,
  empresa: selectedConta.nome,
  email: primeiroContato.email || selectedConta.email || '',
  telefone: primeiroContato.telefone || selectedConta.telefone || '',
  origem: 'site',
  status: 'qualificado',
  conta_id: selectedConta.id,
  contato_id: primeiroContato.id, // ✅ Vincula contato específico
  // ... outros campos
};
```

## Fluxo Completo

1. Usuário clica em "Criar Oportunidade" na página de Contas
2. Sistema busca contatos vinculados à conta
3. Se não houver contatos:
   - Exibe alerta informando necessidade de cadastro
   - Redireciona para página de contatos com conta pré-selecionada
4. Se houver contatos:
   - Usa dados do primeiro contato
   - Cria lead vinculado à conta E ao contato
   - Redireciona para pipeline com modal de criar oportunidade

## Benefícios

1. **Rastreabilidade**: Saber exatamente qual pessoa de contato está relacionada ao lead
2. **Dados Corretos**: Nome, email e telefone do contato específico, não da empresa
3. **Integridade**: Garante que toda oportunidade tem um contato vinculado
4. **UX Melhorada**: Fluxo guiado para cadastro de contato quando necessário

## Deploy

- **Backend**: Heroku v1294 ✅
  - Migração 0030 aplicada com sucesso
  - Campo `contato` disponível no modelo Lead
  
- **Frontend**: Vercel ✅
  - Enviando `contato_id` ao criar lead
  - Validação de contatos implementada

## Testes Recomendados

1. Criar oportunidade a partir de conta COM contatos
2. Criar oportunidade a partir de conta SEM contatos
3. Verificar se contato aparece corretamente no lead criado
4. Verificar se dados do contato (nome, email, telefone) são usados no lead

## Observações

- O sistema usa o PRIMEIRO contato da conta ao criar o lead
- Futuramente pode-se implementar seleção de contato específico
- Campo `contato` é opcional (null=True) para manter compatibilidade com leads antigos
