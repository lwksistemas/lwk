# Análise: Criar Oportunidade a partir de Conta

## Problema Relatado
Ao clicar no botão "Criar Oportunidade" na página de Contas (customers), o sistema:
1. Está abrindo a página de Leads ao invés de ir direto para o Pipeline
2. Não está mostrando apenas os contatos vinculados à empresa

## Análise do Código

### 1. Fluxo Atual (customers/page.tsx)

```typescript
const handleCriarOportunidade = async () => {
  // 1. Busca contatos da conta
  const contatosResponse = await apiClient.get(`/crm-vendas/contatos/?conta_id=${selectedConta.id}`);
  
  // 2. Valida se existe contato
  if (contatosList.length === 0) {
    // Redireciona para cadastrar contato
    router.push(`/loja/${slug}/crm-vendas/contatos?criar=1&conta_id=${selectedConta.id}`);
  }
  
  // 3. Usa primeiro contato
  const primeiroContato = contatosList[0];
  
  // 4. Verifica leads existentes
  const leadsDestaConta = leadsList.filter((lead: any) => lead.conta === selectedConta.id);
  
  // 5. Cria lead com conta e contato
  const leadPayload = {
    nome: primeiroContato.nome,
    empresa: selectedConta.nome,
    conta: selectedConta.id,      // ✅ Correto (sem _id)
    contato: primeiroContato.id,  // ✅ Correto (sem _id)
    // ... outros campos
  };
  
  // 6. Redireciona para pipeline
  router.push(`/loja/${slug}/crm-vendas/pipeline?novo=1&lead_id=${leadResponse.data.id}`);
}
```

### 2. Problema Identificado

**Campos do Payload**: Estava usando `conta_id` e `contato_id`, mas o correto é `conta` e `contato` (ForeignKeys do Django).

**Solução Aplicada**: Corrigido para usar `conta` e `contato` sem o sufixo `_id`.

### 3. Filtro de Contatos

A página de contatos já implementa o filtro corretamente:

```typescript
// contatos/page.tsx
const loadContatos = async (contaId?: number | null) => {
  const url = contaId 
    ? `/crm-vendas/contatos/?conta_id=${contaId}`
    : '/crm-vendas/contatos/';
  const res = await apiClient.get(url);
  setContatos(normalizeListResponse(res.data));
};

// Detecta conta_id na URL
useEffect(() => {
  const contaIdParam = searchParams.get('conta_id');
  if (contaIdParam) {
    const contaId = parseInt(contaIdParam, 10);
    setContaFiltro(contaId);
    loadContatos(contaId);
  }
}, [searchParams]);
```

**Indicador Visual**:
```tsx
{contaFiltro && (
  <div className="flex items-center gap-2">
    <p>Filtrando por conta:</p>
    <span className="badge">{contas.find(c => c.id === contaFiltro)?.nome}</span>
    <button onClick={() => { setContaFiltro(null); loadContatos(null); }}>
      Limpar filtro
    </button>
  </div>
)}
```

## Logs de Debug Adicionados

Para facilitar o diagnóstico, foram adicionados logs detalhados:

```typescript
console.log('🔍 [1/6] Iniciando criação de oportunidade para conta:', selectedConta.nome);
console.log('🔍 [2/6] Buscando contatos da conta ID:', selectedConta.id);
console.log('🔍 [2/6] Contatos encontrados:', contatosList.length, contatosList);
console.log('🔍 [3/6] Usando primeiro contato:', primeiroContato);
console.log('🔍 [4/6] Verificando leads existentes...');
console.log('🔍 [4/6] Leads existentes desta conta:', leadsDestaConta.length);
console.log('🔍 [5/6] Criando lead com payload:', leadPayload);
console.log('🔍 [5/6] Lead criado com sucesso:', leadResponse.data);
console.log('🔍 [6/6] Redirecionando para pipeline com lead_id:', leadResponse.data.id);
```

## Fluxo Esperado

1. Usuário clica em "Criar Oportunidade" na página de Contas
2. Sistema busca contatos vinculados à conta
3. Se não houver contatos:
   - Exibe alerta
   - Redireciona para `/contatos?criar=1&conta_id=X`
   - Página de contatos mostra filtro ativo
4. Se houver contatos:
   - Usa dados do primeiro contato
   - Verifica se já existe lead para a conta
   - Se existir, pergunta se quer criar novo ou usar existente
   - Cria lead com `conta` e `contato` vinculados
   - Redireciona para `/pipeline?novo=1&lead_id=X`
5. Pipeline abre modal de criar oportunidade com lead pré-selecionado

## Testes Recomendados

1. ✅ Criar oportunidade de conta COM contatos
2. ✅ Criar oportunidade de conta SEM contatos (deve redirecionar para cadastro)
3. ✅ Verificar se contato aparece no lead criado
4. ✅ Verificar se filtro de contatos funciona
5. ✅ Verificar se redireciona para pipeline (não para leads)
6. ✅ Verificar logs no console do navegador (F12)

## Deploy

- **Frontend**: Vercel ✅
  - Corrigido campos `conta` e `contato` (sem _id)
  - Adicionados logs detalhados de debug
  - Filtro de contatos já implementado

## Próximos Passos

Se o problema persistir:
1. Abrir console do navegador (F12)
2. Clicar em "Criar Oportunidade"
3. Verificar os logs `🔍 [X/6]` para identificar onde está falhando
4. Verificar se há erros na resposta da API
5. Compartilhar os logs para análise
