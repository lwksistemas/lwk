# ✅ Correção: Criação de Oportunidade com Nome Errado - v1186

**Data:** 21/03/2026  
**Commit:** 5f55bce3  
**URL:** https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers  
**Ambiente:** Produção (Heroku + Vercel)

## 🔴 Problemas Corrigidos

### 1. Lead Criado com Nome Errado
**Antes:** Lead era criado com nome da empresa ao invés do nome do contato  
**Depois:** Lead é criado SEMPRE com nome da pessoa de contato

### 2. Demora para Aparecer Contato
**Antes:** Busca de contatos era feita de forma assíncrona e podia falhar silenciosamente  
**Depois:** Busca de contatos é feita PRIMEIRO e valida existência antes de criar lead

### 3. Criação sem Contato Cadastrado
**Antes:** Permitia criar lead sem contato, usando dados da empresa  
**Depois:** EXIGE que exista pelo menos um contato cadastrado antes de criar oportunidade

## 🔧 Alterações Realizadas

### Arquivo: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`

**Função:** `handleCriarOportunidade()`

#### Mudanças Principais:

1. **Validação de Contato Obrigatória**
```typescript
// 1. PRIMEIRO: Buscar contatos da conta (OBRIGATÓRIO)
const contatosResponse = await apiClient.get(`/crm-vendas/contatos/?conta_id=${selectedConta.id}`);
const contatosList = normalizeListResponse(contatosResponse.data);

// 2. Validar se existe pelo menos um contato
if (contatosList.length === 0) {
  setCreatingOpportunity(false);
  const confirmar = window.confirm(
    '⚠️ Contato Necessário\n\n' +
    'Esta conta não possui contatos cadastrados.\n\n' +
    'Para criar uma oportunidade, é necessário ter pelo menos um contato vinculado à conta.\n\n' +
    'Deseja cadastrar um contato agora?'
  );
  
  if (confirmar) {
    router.push(`/loja/${slug}/crm-vendas/contatos?criar=1&conta_id=${selectedConta.id}`);
  }
  return;
}
```

2. **Uso Correto do Nome do Contato**
```typescript
// 3. Usar dados do primeiro contato
const primeiroContato = contatosList[0] as any;

// 5. Criar Lead vinculado à Conta com dados do CONTATO
const leadResponse = await apiClient.post('/crm-vendas/leads/', {
  nome: primeiroContato.nome, // ✅ Nome da pessoa de contato
  empresa: selectedConta.nome, // Nome da empresa
  email: primeiroContato.email || selectedConta.email || '',
  telefone: primeiroContato.telefone || selectedConta.telefone || '',
  // ...
});
```

3. **Melhor Tratamento de Erros**
```typescript
} catch (err: any) {
  console.error('Erro ao criar oportunidade:', err);
  alert(err.response?.data?.detail || 'Erro ao criar oportunidade.');
  setCreatingOpportunity(false);
}
```

## 📋 Fluxo Corrigido

### Antes (❌ Incorreto):
1. Verificar se já existe lead
2. Tentar buscar contatos (pode falhar)
3. Usar nome da empresa como fallback
4. Criar lead com dados incorretos
5. Redirecionar para pipeline

### Depois (✅ Correto):
1. **Buscar contatos PRIMEIRO**
2. **Validar se existe contato (obrigatório)**
3. Se não houver contato, mostrar mensagem e redirecionar para cadastro
4. Verificar se já existe lead
5. **Criar lead com dados do CONTATO**
6. Redirecionar para pipeline

## 🚀 Deploy

### Status:
- ✅ Código corrigido
- ✅ Commit realizado (5f55bce3)
- ✅ Push para GitHub
- ⏳ Deploy automático no Vercel (em andamento)

### Verificação:
Após deploy, testar em:
- URL: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers
- Ação: Clicar em "Visualizar" conta → "Criar Oportunidade"
- Validar:
  - [ ] Se não houver contato, mostra mensagem de erro
  - [ ] Se houver contato, cria lead com nome correto
  - [ ] Lead aparece com nome da pessoa (não da empresa)
  - [ ] Redireciona para pipeline corretamente

## 📝 Notas Técnicas

### Tipagem TypeScript:
- Adicionado `as any` para `primeiroContato` e `leadsDestaConta[0]` para evitar erros de tipo
- Mantido uso de `normalizeListResponse()` para padronizar respostas da API

### Compatibilidade:
- Mantido suporte para respostas da API em formato array ou objeto com `results`
- Mantido fallback para email/telefone da empresa se contato não tiver

### UX:
- Mensagem clara quando não há contato cadastrado
- Opção de redirecionar para cadastro de contato
- Feedback visual durante todo o processo (botão "Criando...")

## 🎯 Resultado Esperado

Após esta correção:
1. ✅ Leads sempre criados com nome correto (pessoa de contato)
2. ✅ Não permite criar oportunidade sem contato cadastrado
3. ✅ Mensagem clara e direcionamento para cadastro de contato
4. ✅ Processo mais rápido e confiável
5. ✅ Melhor experiência do usuário

## 📚 Documentação Relacionada

- Análise completa: `ANALISE_PROBLEMA_CRIACAO_OPORTUNIDADE_NOME_ERRADO.md`
- Modelo Lead: `backend/crm_vendas/models.py` (linha 95-150)
- Modelo Contato: `backend/crm_vendas/models.py` (linha 152-185)
- Serializer Lead: `backend/crm_vendas/serializers.py` (linha 180-210)
