# 📋 Plano de Refatoração - Sistema de Suporte

## 🎯 Objetivo
Aplicar boas práticas de programação no sistema de suporte (banco de dados isolado), seguindo o padrão estabelecido nos apps de loja e Superadmin.

---

## 📊 Análise Atual

### Frontend:

| Arquivo | Linhas | Complexidade | Prioridade |
|---------|--------|--------------|------------|
| **suporte/dashboard/page.tsx** | ~500 | 🔴 Alta | 🔥 Alta |
| **suporte/login/page.tsx** | ~230 | 🟡 Média | ⚠️ Média |

**Total**: ~730 linhas para refatorar

### Backend:
| Arquivo | Linhas | Status |
|---------|--------|--------|
| models.py | ~80 | ✅ Bem organizado |
| views.py | ~150 | ✅ Bem organizado |
| serializers.py | ~25 | ✅ Bem organizado |

**Backend**: Já está bem estruturado! ✅

---

## 🚀 Estratégia de Refatoração

### Fase 1: Dashboard do Suporte (Prioridade Alta)

#### suporte/dashboard/page.tsx (~500 linhas)

**Componentes Identificados para Extração:**

1. **ModalAtendimento** (~200 linhas)
   - Visualização completa do chamado
   - Histórico de respostas
   - Área de resposta
   - Ações (iniciar, resolver)

2. **CardEstatisticas** (~50 linhas)
   - Cards de métricas (Total, Abertos, Em Andamento, Resolvidos)
   - Componente reutilizável

3. **TabelaChamados** (~100 linhas)
   - Tabela com lista de chamados
   - Filtros e ordenação
   - Ações por linha

**Estrutura Proposta:**
```
frontend/components/suporte/
├── dashboard/
│   ├── ModalAtendimento.tsx      (~200 linhas)
│   ├── CardEstatisticas.tsx      (~50 linhas)
│   ├── TabelaChamados.tsx        (~100 linhas)
│   └── index.ts
└── BotaoSuporte.tsx              (já existe)
```

**Redução Esperada**: 500 → ~150 linhas (70% menor)

---

### Fase 2: Login do Suporte (Prioridade Média)

#### suporte/login/page.tsx (~230 linhas)

**Componentes Identificados para Extração:**

1. **ModalRecuperarSenha** (~80 linhas)
   - Formulário de recuperação
   - Validação de email
   - Mensagens de sucesso/erro

2. **FormLogin** (~60 linhas)
   - Formulário de login
   - Validação
   - Estados de loading

**Estrutura Proposta:**
```
frontend/components/suporte/
├── login/
│   ├── ModalRecuperarSenha.tsx   (~80 linhas)
│   ├── FormLogin.tsx             (~60 linhas)
│   └── index.ts
```

**Redução Esperada**: 230 → ~90 linhas (61% menor)

---

## 📈 Resultados Esperados

### Antes da Refatoração:
- 2 arquivos com ~730 linhas
- Média de 365 linhas por arquivo
- Difícil manutenção
- Código inline

### Depois da Refatoração:
- 2 arquivos principais (~240 linhas)
- 5 componentes modulares (~490 linhas)
- Total: ~730 linhas organizadas
- Fácil manutenção
- Código reutilizável

**Redução no arquivo principal**: ~67% em média  
**Ganho de modularidade**: 100%

---

## 🎯 Benefícios

1. **Manutenibilidade**: Cada componente em seu próprio arquivo
2. **Testabilidade**: Componentes isolados e testáveis
3. **Reutilização**: Componentes podem ser compartilhados
4. **Legibilidade**: Código mais fácil de entender
5. **Isolamento**: Sistema de suporte com banco isolado bem organizado

---

## 📝 Checklist de Execução

### Fase 1 - Dashboard (Alta Prioridade)
- [ ] Criar estrutura de pastas
- [ ] Extrair ModalAtendimento
  - [ ] Visualização do chamado
  - [ ] Histórico de respostas
  - [ ] Área de resposta
  - [ ] Ações (iniciar, resolver)
- [ ] Extrair CardEstatisticas
  - [ ] Componente de card reutilizável
  - [ ] Props para dados dinâmicos
- [ ] Extrair TabelaChamados
  - [ ] Tabela com lista
  - [ ] Ações por linha
- [ ] Criar index.ts
- [ ] Atualizar dashboard/page.tsx
- [ ] Testar funcionalidades
- [ ] Deploy

### Fase 2 - Login (Média Prioridade)
- [ ] Extrair ModalRecuperarSenha
  - [ ] Formulário de recuperação
  - [ ] Validação
  - [ ] Mensagens
- [ ] Extrair FormLogin
  - [ ] Formulário de login
  - [ ] Validação
  - [ ] Estados
- [ ] Criar index.ts
- [ ] Atualizar login/page.tsx
- [ ] Testar funcionalidades
- [ ] Deploy

---

## 🔍 Detalhes Técnicos

### ModalAtendimento.tsx

**Props:**
```typescript
interface ModalAtendimentoProps {
  chamado: Chamado | null;
  isOpen: boolean;
  onClose: () => void;
  onIniciarAtendimento: (id: number) => Promise<void>;
  onResolver: (id: number) => Promise<void>;
  onEnviarResposta: (id: number, mensagem: string) => Promise<void>;
  onReload: () => void;
}
```

**Funcionalidades:**
- Exibir informações completas do chamado
- Mostrar histórico de respostas
- Permitir adicionar nova resposta
- Ações: iniciar atendimento, resolver
- Loading states
- Validações

---

### CardEstatisticas.tsx

**Props:**
```typescript
interface CardEstatisticasProps {
  titulo: string;
  valor: number;
  cor: 'blue' | 'yellow' | 'green' | 'gray';
}
```

**Funcionalidades:**
- Card reutilizável para métricas
- Cores dinâmicas
- Formatação de números

---

### TabelaChamados.tsx

**Props:**
```typescript
interface TabelaChamadosProps {
  chamados: Chamado[];
  loading: boolean;
  onAtender: (chamado: Chamado) => void;
}
```

**Funcionalidades:**
- Tabela responsiva
- Badges de status e prioridade
- Ações por linha
- Estado de loading
- Empty state

---

### ModalRecuperarSenha.tsx

**Props:**
```typescript
interface ModalRecuperarSenhaProps {
  isOpen: boolean;
  onClose: () => void;
}
```

**Funcionalidades:**
- Formulário de recuperação
- Validação de email
- Estados de loading
- Mensagens de sucesso/erro
- Auto-close após sucesso

---

### FormLogin.tsx

**Props:**
```typescript
interface FormLoginProps {
  onSubmit: (credentials: { username: string; password: string }) => Promise<void>;
  loading: boolean;
  error: string;
}
```

**Funcionalidades:**
- Formulário de login
- Validação de campos
- Estados de loading
- Exibição de erros

---

## 🚦 Status Atual

**Fase**: ✅ 100% COMPLETO!  
**Resultado**: Refatoração finalizada com sucesso!

### ✅ Progresso:
- [x] Criar estrutura de pastas ✅
- [x] Fase 1 - Dashboard (Alta Prioridade) ✅
  - [x] Extrair ModalAtendimento ✅
  - [x] Extrair CardEstatisticas ✅
  - [x] Extrair TabelaChamados ✅
  - [x] Criar index.ts ✅
  - [x] Atualizar dashboard/page.tsx ✅
  - [x] Testar funcionalidades ✅
  - [x] Deploy ✅
- [x] Fase 2 - Login (Média Prioridade) ✅
  - [x] Extrair ModalRecuperarSenha ✅
  - [x] Extrair FormLogin ✅
  - [x] Criar index.ts ✅
  - [x] Atualizar login/page.tsx ✅
  - [x] Testar funcionalidades ✅
  - [x] Deploy ✅

---

**Status**: ✅ 100% COMPLETO - Sistema de suporte totalmente refatorado!  
**Pronto para**: Produção  
**Última Atualização**: 04/02/2026
