# Guia: Como Criar Oportunidade a Partir de uma Conta

## Data
19/03/2026

## Situação Atual

Você cadastrou:
- ✅ **Conta** (empresa) em `/crm-vendas/customers`
- ✅ **Contato** (pessoa) em `/crm-vendas/contatos`

Agora quer criar uma **Oportunidade** (negócio) para essa empresa.

## Problema

O sistema CRM segue o fluxo Salesforce:
```
Lead → Conta → Contato → Oportunidade
```

Para criar uma Oportunidade, você precisa de um **Lead** vinculado à Conta.

## Solução Atual (Manual)

### Passo 1: Criar um Lead vinculado à Conta

1. Acesse: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/leads
2. Clique em "Novo Lead"
3. Preencha os dados:
   - **Nome**: Nome do contato principal
   - **Empresa**: Nome da conta que você criou
   - **Email**: Email do contato
   - **Telefone**: Telefone do contato
   - **Origem**: Escolha a origem (ex: "Site", "Indicação")
   - **Status**: "Qualificado" (já que você já tem a conta criada)
   - **Conta**: Selecione a conta que você criou
4. Clique em "Salvar"

### Passo 2: Criar Oportunidade a partir do Lead

1. Na lista de Leads, clique no lead que você acabou de criar
2. Clique em "Criar Oportunidade"
3. Preencha:
   - **Título**: Nome do negócio (ex: "Venda de Sistema CRM")
   - **Valor**: Valor estimado do negócio
   - **Etapa**: Escolha a etapa inicial (ex: "Prospecção")
   - **Produtos/Serviços**: Adicione os itens da oportunidade
4. Clique em "Salvar"

## Solução Melhorada (A Implementar)

### Opção A: Botão "Criar Oportunidade" na Conta

Adicionar um botão na visualização da Conta que:
1. Cria automaticamente um Lead vinculado à Conta
2. Abre o modal de criar Oportunidade
3. Pré-preenche os dados com informações da Conta

### Opção B: Criar Oportunidade Direto da Conta

Permitir criar Oportunidade diretamente da Conta, sem precisar de Lead intermediário:
1. Modificar modelo `Oportunidade` para aceitar `conta` opcional
2. Adicionar botão "Nova Oportunidade" na página de Contas
3. Modal cria oportunidade vinculada à conta

### Opção C: Atalho na Página de Contas

Adicionar um botão "Criar Lead + Oportunidade" que:
1. Abre modal com dados da Conta pré-preenchidos
2. Permite criar Lead e Oportunidade em um único fluxo
3. Vincula tudo automaticamente

## Recomendação

**Implementar Opção A** por ser:
- Mais rápida de implementar
- Mantém a integridade do fluxo CRM
- Não requer mudanças no modelo de dados
- Facilita o processo para o usuário

## Arquivos a Modificar

### Frontend
1. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`
   - Adicionar botão "Criar Oportunidade" na visualização da conta
   - Criar função que cria Lead automaticamente
   - Redirecionar para pipeline com modal de criar oportunidade

### Backend
Nenhuma mudança necessária (usar endpoints existentes)

## Fluxo Proposto

```typescript
// Ao clicar em "Criar Oportunidade" na Conta
async function criarOportunidadeParaConta(conta: Conta) {
  // 1. Criar Lead vinculado à Conta
  const lead = await apiClient.post('/crm-vendas/leads/', {
    nome: conta.nome,
    empresa: conta.nome,
    email: conta.email,
    telefone: conta.telefone,
    origem: 'site',
    status: 'qualificado',
    conta_id: conta.id,
  });
  
  // 2. Redirecionar para pipeline com modal de criar oportunidade
  router.push(`/loja/${slug}/crm-vendas/pipeline?novo=1&lead_id=${lead.data.id}`);
}
```

## Próximos Passos

1. Implementar botão "Criar Oportunidade" na visualização da Conta
2. Criar função para criar Lead automaticamente
3. Redirecionar para pipeline com modal aberto
4. Testar fluxo completo
5. Documentar para usuários

## Observações

- O Lead intermediário é necessário para manter a integridade do CRM
- Leads podem ser "qualificados" automaticamente quando criados via Conta
- O fluxo manual atual funciona, mas é trabalhoso
- A solução automatizada melhora significativamente a UX
