# Análise: Problema na Criação de Oportunidade - Nome Errado e Demora nos Contatos

**Data:** 21/03/2026  
**URL Afetada:** https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers  
**Ambiente:** Produção (Heroku + Vercel)

## 🔴 Problema Relatado

Ao criar uma nova oportunidade em "Detalhes da Conta" (modal de visualização):
1. ✅ Lead está sendo criado com o **nome errado**
2. ✅ Está **demorando** para aparecer o contato vinculado à empresa
3. ✅ Só pode criar o lead a partir da empresa após criar no botão "Criar"

## 🔍 Análise do Código

### Arquivo: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`

**Função problemática:** `handleCriarOportunidade()` (linhas 283-360)

### Problema 1: Nome Errado no Lead

**Código atual (linha 340):**
```typescript
// Buscar contatos da conta para usar dados do primeiro contato
let nomeContato = selectedConta.nome; // Fallback: usar nome da empresa
let emailContato = selectedConta.email || ''; // Fallback: email da empresa
let telefoneContato = selectedConta.telefone || ''; // Fallback: telefone da empresa

try {
  const contatosResponse = await apiClient.get(`/crm-vendas/contatos/?conta_id=${selectedConta.id}`);
  const contatosList = Array.isArray(contatosResponse.data) 
    ? contatosResponse.data 
    : contatosResponse.data?.results || [];
  
  if (contatosList.length > 0) {
    const primeiroContato = contatosList[0];
    nomeContato = primeiroContato.nome; // Usar nome do contato
    emailContato = primeiroContato.email || selectedConta.email || ''; // Priorizar email do contato
    telefoneContato = primeiroContato.telefone || selectedConta.telefone || ''; // Priorizar telefone do contato
  }
} catch (err) {
  console.log('Não foi possível buscar contatos, usando dados da empresa');
}

// Criar Lead vinculado à Conta
const leadResponse = await apiClient.post('/crm-vendas/leads/', {
  nome: nomeContato, // ❌ PROBLEMA: Usando nome do contato ou empresa
  empresa: selectedConta.nome, // Nome da empresa
  // ...
});
```

**Problema identificado:**
- O campo `nome` do Lead está sendo preenchido com o nome do **contato** (pessoa) ou da **empresa**
- Isso está **ERRADO** porque o campo `nome` do Lead deveria ser o nome da **pessoa de contato**
- Se não houver contato cadastrado, está usando o nome da empresa, o que não faz sentido

### Problema 2: Demora para Aparecer Contato

**Código atual:**
```typescript
try {
  const contatosResponse = await apiClient.get(`/crm-vendas/contatos/?conta_id=${selectedConta.id}`);
  // ...
} catch (err) {
  console.log('Não foi possível buscar contatos, usando dados da empresa');
}
```

**Problema identificado:**
- A busca de contatos é feita **de forma assíncrona** dentro de um `try/catch`
- Se houver erro ou demora na API, o código continua e cria o lead com dados da empresa
- Não há **feedback visual** para o usuário de que está buscando contatos
- Não há **validação** se existe contato antes de criar o lead

### Problema 3: Lógica de Criação Confusa

**Fluxo atual:**
1. Verifica se já existe lead para a conta
2. Se existir, pergunta se quer criar novo ou usar existente
3. Busca contatos da conta (pode falhar silenciosamente)
4. Cria lead com dados do contato (ou empresa se não houver)
5. Redireciona para pipeline

**Problemas:**
- ❌ Não valida se existe contato antes de criar lead
- ❌ Não mostra loading enquanto busca contatos
- ❌ Não exige que tenha contato cadastrado
- ❌ Usa nome da empresa como fallback (incorreto)

## ✅ Solução Proposta

### 1. Validar Existência de Contato ANTES de Criar Lead

```typescript
// 1. Buscar contatos PRIMEIRO
const contatosResponse = await apiClient.get(`/crm-vendas/contatos/?conta_id=${selectedConta.id}`);
const contatosList = normalizeListResponse(contatosResponse.data);

// 2. Se não houver contato, EXIGIR criação
if (contatosList.length === 0) {
  const confirmar = window.confirm(
    'Esta conta não possui contatos cadastrados.\n\n' +
    'É necessário cadastrar um contato antes de criar uma oportunidade.\n\n' +
    'Deseja cadastrar um contato agora?'
  );
  
  if (confirmar) {
    // Redirecionar para página de contatos com conta pré-selecionada
    router.push(`/loja/${slug}/crm-vendas/contatos?criar=1&conta_id=${selectedConta.id}`);
  }
  return;
}

// 3. Se houver múltiplos contatos, permitir escolher
let contatoSelecionado = contatosList[0];
if (contatosList.length > 1) {
  // Mostrar modal para selecionar contato
  // (implementar depois se necessário)
}

// 4. Criar lead com dados do contato
const leadResponse = await apiClient.post('/crm-vendas/leads/', {
  nome: contatoSelecionado.nome, // ✅ Nome da pessoa
  empresa: selectedConta.nome, // Nome da empresa
  email: contatoSelecionado.email || '',
  telefone: contatoSelecionado.telefone || '',
  // ...
});
```

### 2. Adicionar Feedback Visual

```typescript
setCreatingOpportunity(true);

try {
  // Mostrar que está buscando contatos
  // (já está usando setCreatingOpportunity)
  
  // Buscar contatos...
  // Validar...
  // Criar lead...
  
} catch (err: any) {
  alert(err.response?.data?.detail || 'Erro ao criar oportunidade.');
} finally {
  setCreatingOpportunity(false);
}
```

### 3. Melhorar Mensagens de Erro

```typescript
if (contatosList.length === 0) {
  alert(
    '⚠️ Contato Necessário\n\n' +
    'Esta conta não possui contatos cadastrados.\n\n' +
    'Para criar uma oportunidade, é necessário ter pelo menos um contato vinculado à conta.\n\n' +
    'Por favor, cadastre um contato primeiro.'
  );
  setCreatingOpportunity(false);
  return;
}
```

## 📋 Checklist de Correção

- [ ] Validar existência de contato ANTES de criar lead
- [ ] Usar SEMPRE nome do contato (nunca nome da empresa)
- [ ] Adicionar mensagem clara se não houver contato
- [ ] Manter feedback visual durante todo o processo
- [ ] Testar em produção (Heroku + Vercel)
- [ ] Verificar se contatos aparecem corretamente
- [ ] Confirmar que nome do lead está correto

## 🚀 Deploy

1. Corrigir código no frontend
2. Fazer commit e push
3. Deploy automático no Vercel
4. Testar na URL: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers
