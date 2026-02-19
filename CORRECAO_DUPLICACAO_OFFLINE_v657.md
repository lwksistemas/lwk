# Correção de Duplicação em Cadastros Offline - v657

## Problema Identificado

Ao criar profissionais, pacientes ou procedimentos em modo offline (ou com conexão instável), os registros estavam sendo duplicados na fila de sincronização.

### Causa Raiz

O sistema tinha dois pontos onde adicionava itens na fila:

1. **Modo Offline Explícito**: Quando `navigator.onLine === false`
2. **Erro de Rede no Modo Online**: Quando tentava salvar online mas falhava por erro de rede

**Problema**: Se o usuário clicasse múltiplas vezes no botão "Salvar" ou se houvesse erro de rede, o mesmo item era adicionado várias vezes na fila.

### Exemplo do Problema

```
Usuário cria "Dra. Ivone Felix" → Adiciona na fila (ID: 15)
Usuário clica em "Salvar" novamente → Adiciona na fila (ID: 16) ❌ DUPLICADO
Erro de rede ao salvar → Adiciona na fila (ID: 17) ❌ DUPLICADO
```

Resultado: 3 itens na fila para o mesmo profissional!

## Solução Implementada

### 1. Verificação de Duplicação no Modo Offline

Antes de adicionar na fila, o sistema agora verifica se já existe um item similar:

```typescript
// Verificar se já existe na lista local (evitar duplicação)
if (!editing || (editing && editing.id < 0)) {
  const jaExisteLocal = list.some(p => 
    p.name.toLowerCase() === form.name.trim().toLowerCase() && 
    p.specialty.toLowerCase() === form.specialty.trim().toLowerCase()
  );
  
  if (jaExisteLocal) {
    setError("Este profissional já foi adicionado. Aguarde a sincronização.");
    setSaving(false);
    return;
  }
}
```

### 2. Verificação de Duplicação em Erro de Rede

Quando há erro de rede durante salvamento online:

```typescript
// Verificar se já existe na lista local (evitar duplicação)
const jaExisteLocal = editing 
  ? list.some(p => p.id === editing.id) 
  : list.some(p => p.name.toLowerCase() === form.name.trim().toLowerCase());

if (jaExisteLocal && !editing) {
  setError("Este profissional já foi adicionado offline. Aguarde a sincronização.");
  setSaving(false);
  return;
}
```

### 3. Logs de Debug

Adicionados logs de erro para facilitar diagnóstico:

```typescript
} catch (err) {
  console.error("Erro ao salvar offline:", err);
  setError("Erro ao salvar localmente. Tente novamente.");
}
```

## Arquivos Modificados

### 1. Profissionais
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/profissionais/page.tsx`

**Mudanças**:
- Verificação de duplicação por nome + especialidade no modo offline
- Verificação de duplicação por nome no erro de rede
- Logs de erro detalhados

### 2. Pacientes
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/pacientes/page.tsx`

**Mudanças**:
- Verificação de duplicação por nome + telefone (se fornecido) no modo offline
- Verificação de duplicação por nome no erro de rede
- Logs de erro detalhados

### 3. Procedimentos
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/clinica-beleza/procedimentos/page.tsx`

**Mudanças**:
- Verificação de duplicação por nome no modo offline
- Verificação de duplicação por nome no erro de rede
- Logs de erro detalhados

## Como Funciona Agora

### Cenário 1: Usuário Offline
1. Usuário cria "Dra. Ivone Felix"
2. Sistema verifica se já existe na lista local
3. Se não existe: adiciona na fila e na lista local
4. Se existe: mostra erro "Este profissional já foi adicionado. Aguarde a sincronização."

### Cenário 2: Erro de Rede
1. Usuário tenta salvar online
2. Ocorre erro de rede (timeout, sem conexão, etc.)
3. Sistema verifica se já existe na lista local
4. Se não existe: adiciona na fila e na lista local
5. Se existe: mostra erro "Este profissional já foi adicionado offline. Aguarde a sincronização."

### Cenário 3: Múltiplos Cliques
1. Usuário clica em "Salvar"
2. Botão fica desabilitado (`saving = true`)
3. Se usuário clicar novamente, nada acontece (botão desabilitado)
4. Após salvar, botão é reabilitado

## Testando a Correção

### Teste 1: Criar Offline
1. Desconecte a internet (modo avião)
2. Acesse: https://lwksistemas.com.br/loja/clinica-luiz-000172/clinica-beleza/profissionais
3. Clique em "Novo Profissional"
4. Preencha: Nome "Teste Duplicação", Especialidade "Teste"
5. Clique em "Salvar"
6. Tente criar novamente com o mesmo nome
7. **Resultado esperado**: Erro "Este profissional já foi adicionado. Aguarde a sincronização."

### Teste 2: Erro de Rede
1. Use DevTools para simular rede lenta (Throttling: Slow 3G)
2. Crie um profissional
3. Se der timeout, tente salvar novamente
4. **Resultado esperado**: Erro "Este profissional já foi adicionado offline. Aguarde a sincronização."

### Teste 3: Sincronização
1. Com itens na fila, conecte à internet
2. Clique no botão de sincronização (🔄)
3. Verifique o console (F12) para logs
4. **Resultado esperado**: Itens sincronizados sem duplicação no servidor

## Limpando a Fila Atual

Se você já tem itens duplicados na fila:

### Opção 1: Limpar Tudo
1. Clique no botão de lixeira (🗑️) no indicador offline
2. Confirme a ação
3. Recrie os profissionais (apenas uma vez cada)

### Opção 2: Sincronizar e Limpar Duplicados
1. Sincronize a fila (botão 🔄)
2. Se houver erros de duplicação, o backend vai rejeitar
3. Limpe a fila (botão 🗑️)
4. Verifique no backend quais foram criados
5. Remova duplicados manualmente se necessário

## Critérios de Duplicação

### Profissionais
- **Nome** (case-insensitive) + **Especialidade** (case-insensitive)
- Exemplo: "Dra. Ivone Felix" + "Dermatologista" = duplicado

### Pacientes
- **Nome** (case-insensitive) + **Telefone** (se fornecido)
- Exemplo: "João Silva" + "11 98765-4321" = duplicado
- Se não tiver telefone, apenas nome

### Procedimentos
- **Nome** (case-insensitive)
- Exemplo: "Limpeza de Pele" = duplicado

## Observações Importantes

### 1. Verificação Local
A verificação é feita apenas na lista local (IndexedDB). Se você:
- Limpar o cache do navegador
- Usar outro dispositivo
- Usar modo anônimo

A verificação não vai funcionar porque a lista local estará vazia.

### 2. Sincronização Pendente
Se você tem itens na fila aguardando sincronização, eles aparecem na lista com ID negativo (ex: -1708358419000). A verificação considera esses itens.

### 3. Edição vs Criação
- **Criação**: Verifica duplicação por nome/especialidade
- **Edição**: Não verifica duplicação (permite editar o nome)

### 4. Case-Insensitive
A verificação ignora maiúsculas/minúsculas:
- "Dra. Ivone Felix" = "dra. ivone felix" = "DRA. IVONE FELIX"

## Deploy Realizado

- **Frontend**: v657 - Deploy concluído no Vercel
- **URL**: https://lwksistemas.com.br
- **Data**: 19/02/2026

## Próximos Passos

1. ✅ Limpe a fila atual (botão 🗑️)
2. ✅ Verifique se os profissionais já foram criados no servidor
3. ✅ Remova duplicados manualmente se necessário
4. ✅ Teste criar novos profissionais offline
5. ✅ Verifique se a duplicação foi corrigida
6. ✅ Configure horários de trabalho para cada profissional
7. ✅ Teste a agenda com os logs de debug implementados

## Suporte

Se ainda houver problemas de duplicação:
1. Abra o Console (F12)
2. Tente criar um item duplicado
3. Copie os logs de erro
4. Envie para análise
