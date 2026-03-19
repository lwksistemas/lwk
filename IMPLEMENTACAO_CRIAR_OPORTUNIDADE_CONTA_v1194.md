# Implementação: Criar Oportunidade Diretamente da Conta - v1194

## Data
19/03/2026

## Objetivo
Facilitar a criação de oportunidades a partir de contas existentes, eliminando a necessidade de criar manualmente um lead intermediário.

## Problema Identificado

O usuário cadastrou:
- ✅ Conta (empresa) em `/crm-vendas/customers`
- ✅ Contato (pessoa) em `/crm-vendas/contatos`

Mas não conseguia criar uma Oportunidade porque o sistema exige um Lead vinculado à Conta.

### Fluxo Antigo (Manual)
1. Criar Conta
2. Ir para Leads
3. Criar Lead manualmente vinculado à Conta
4. Criar Oportunidade a partir do Lead

**Problema**: Processo trabalhoso e não intuitivo

## Solução Implementada

### Botão "Criar Oportunidade" na Visualização da Conta

Adicionado botão verde "Criar Oportunidade" no modal de visualização da conta que:
1. Cria automaticamente um Lead vinculado à Conta
2. Redireciona para o Pipeline com modal de criar oportunidade aberto
3. Pré-seleciona o Lead criado no formulário

### Fluxo Novo (Automatizado)
1. Criar Conta
2. Visualizar Conta
3. Clicar em "Criar Oportunidade"
4. Sistema cria Lead automaticamente
5. Modal de criar oportunidade abre com Lead pré-selecionado
6. Preencher dados da oportunidade e salvar

**Benefício**: Processo simplificado em 1 clique

## Implementação Técnica

### 1. Frontend - Página de Contas
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`

#### Estado Adicionado
```typescript
const [creatingOpportunity, setCreatingOpportunity] = useState(false);
```

#### Função Criada
```typescript
const handleCriarOportunidade = async () => {
  if (!selectedConta) return;
  
  try {
    setCreatingOpportunity(true);
    
    // Criar Lead vinculado à Conta
    const leadResponse = await apiClient.post('/crm-vendas/leads/', {
      nome: selectedConta.nome,
      empresa: selectedConta.nome,
      email: selectedConta.email || '',
      telefone: selectedConta.telefone || '',
      origem: 'site',
      status: 'qualificado',
      conta_id: selectedConta.id,
      cpf_cnpj: selectedConta.cnpj || '',
      cep: selectedConta.cep || '',
      logradouro: selectedConta.logradouro || '',
      numero: selectedConta.numero || '',
      complemento: selectedConta.complemento || '',
      bairro: selectedConta.bairro || '',
      cidade: selectedConta.cidade || '',
      uf: selectedConta.uf || '',
    });
    
    // Redirecionar para pipeline com modal de criar oportunidade
    router.push(`/loja/${slug}/crm-vendas/pipeline?novo=1&lead_id=${leadResponse.data.id}`);
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Erro ao criar oportunidade.');
    setCreatingOpportunity(false);
  }
};
```

#### Botão Adicionado
```tsx
<button
  type="button"
  onClick={handleCriarOportunidade}
  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:opacity-50 flex items-center gap-2"
  disabled={creatingOpportunity}
>
  <Plus size={16} />
  {creatingOpportunity ? 'Criando...' : 'Criar Oportunidade'}
</button>
```

### 2. Frontend - Página de Pipeline
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`

#### Modificação no useEffect
```typescript
useEffect(() => {
  const leadIdParam = searchParams.get('lead_id');
  if (searchParams.get('novo') === '1') {
    setModalCriar(true);
    // Se veio com lead_id, pré-selecionar
    if (leadIdParam) {
      setFormCriar((f) => ({ ...f, lead_id: leadIdParam }));
    }
    router.replace(`/loja/${slug}/crm-vendas/pipeline`, { scroll: false });
  }
}, [searchParams, router, slug]);
```

## Como Usar

### Passo 1: Visualizar a Conta
1. Acesse: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers
2. Clique no ícone de "olho" (👁️) na conta desejada

### Passo 2: Criar Oportunidade
1. No modal de visualização, clique no botão verde "Criar Oportunidade"
2. Aguarde o redirecionamento (sistema cria Lead automaticamente)
3. Modal de criar oportunidade abre com Lead pré-selecionado

### Passo 3: Preencher Dados da Oportunidade
1. **Título**: Nome do negócio (ex: "Venda de Sistema CRM")
2. **Valor**: Valor estimado do negócio
3. **Etapa**: Escolha a etapa inicial (ex: "Prospecção")
4. **Produtos/Serviços**: Adicione os itens da oportunidade
5. Clique em "Salvar"

## Dados do Lead Criado Automaticamente

O Lead criado herda os dados da Conta:
- **Nome**: Nome da conta
- **Empresa**: Nome da conta
- **Email**: Email da conta
- **Telefone**: Telefone da conta
- **CPF/CNPJ**: CNPJ da conta
- **Origem**: "site" (padrão)
- **Status**: "qualificado" (já que a conta existe)
- **Conta**: Vinculado à conta
- **Endereço completo**: CEP, logradouro, número, complemento, bairro, cidade, UF

## Benefícios

✅ Processo simplificado: 1 clique vs. 3 passos manuais
✅ Menos erros: Dados copiados automaticamente da conta
✅ Experiência intuitiva: Fluxo natural do CRM
✅ Mantém integridade: Lead intermediário preserva o fluxo Salesforce
✅ Dados completos: Endereço e informações da conta são copiados

## Arquivos Modificados

1. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`
   - Adicionado estado `creatingOpportunity`
   - Criada função `handleCriarOportunidade`
   - Adicionado botão "Criar Oportunidade" no modal de visualização

2. `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`
   - Modificado useEffect para aceitar parâmetro `lead_id`
   - Pré-seleciona lead quando vem da conta

3. `GUIA_CRIAR_OPORTUNIDADE_A_PARTIR_CONTA.md` (NOVO)
   - Documentação do fluxo manual e automatizado

4. `IMPLEMENTACAO_CRIAR_OPORTUNIDADE_CONTA_v1194.md` (NOVO)
   - Documentação técnica da implementação

## Deploy

- **Versão**: v1194 (frontend)
- **Data**: 19/03/2026
- **Status**: ✅ Sucesso
- **URL**: https://lwksistemas.com.br

## Testes Realizados

✅ Botão aparece no modal de visualização da conta
✅ Botão fica desabilitado durante criação (loading state)
✅ Lead é criado com dados da conta
✅ Redirecionamento para pipeline funciona
✅ Modal de criar oportunidade abre automaticamente
✅ Lead é pré-selecionado no formulário

## Próximos Passos

- Testar criação completa de oportunidade
- Validar se dados do lead são salvos corretamente
- Considerar adicionar botão também na lista de contas (não apenas no modal)
- Adicionar tooltip explicativo no botão
- Considerar adicionar confirmação antes de criar lead

## Observações

- O Lead criado tem status "qualificado" automaticamente
- A origem do lead é "site" por padrão (pode ser configurável no futuro)
- O Lead fica vinculado à Conta permanentemente
- Se a conta já tiver leads, um novo lead é criado (não reutiliza existente)
- O botão verde destaca a ação principal (criar oportunidade)
- Loading state ("Criando...") melhora feedback visual
