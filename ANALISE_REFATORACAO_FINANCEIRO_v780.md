# Análise e Plano de Refatoração - Página Financeiro (v780)

**Data**: 02/03/2026  
**Página**: `/superadmin/financeiro`  
**Linhas Atuais**: 673 linhas  
**Meta**: ~150 linhas

---

## 📊 Análise da Página Atual

### Problemas Identificados

1. **Código Monolítico**: 673 linhas em um único arquivo
2. **Componentes Inline**: `StatCard` e `AssinaturaCard` definidos dentro do arquivo
3. **Lógica Misturada**: UI + lógica de negócio + chamadas API
4. **Duplicação**: Lógica similar para Asaas e Mercado Pago
5. **Falta de Separação**: Asaas e Mercado Pago misturados na mesma view

### Funcionalidades Principais

1. **Estatísticas**: Receita total, assinaturas ativas, pagamentos pendentes
2. **Assinaturas**: Lista de assinaturas (Asaas + Mercado Pago)
3. **Pagamentos**: Lista de todos os pagamentos com filtros
4. **Ações Asaas**:
   - Baixar boleto
   - Copiar PIX
   - Atualizar status
   - Nova cobrança manual
   - Excluir cobrança
5. **Ações Mercado Pago**:
   - Baixar boleto (via API)
   - Gerar PIX
   - Copiar PIX
   - Atualizar status (sync com MP)

---

## 🎯 Proposta de Refatoração

### Estrutura Proposta

```
hooks/
  ├── useFinanceiroStats.ts          # Estatísticas gerais
  ├── useAssinaturas.ts              # Lista de assinaturas
  ├── usePagamentos.ts               # Lista de pagamentos
  ├── useAsaasActions.ts             # Ações específicas Asaas
  └── useMercadoPagoActions.ts       # Ações específicas Mercado Pago

components/superadmin/financeiro/
  ├── FinanceiroStats.tsx            # Cards de estatísticas
  ├── AssinaturasTab.tsx             # Tab de assinaturas
  ├── PagamentosTab.tsx              # Tab de pagamentos
  ├── AssinaturaCard.tsx             # Card individual (já existe)
  ├── AssinaturaAsaas.tsx            # Seção Asaas do card
  ├── AssinaturaMercadoPago.tsx      # Seção Mercado Pago do card
  ├── PagamentosTable.tsx            # Tabela de pagamentos
  ├── PagamentosFiltros.tsx          # Filtros de status
  ├── ModalNovaCobranca.tsx          # (já existe)
  ├── ModalConfirmarExclusao.tsx     # (já existe)
  └── index.ts                       # Exports centralizados

app/(dashboard)/superadmin/financeiro/
  └── page.tsx                       # Página orquestradora (~150 linhas)
```

---

## 🔧 Detalhamento dos Hooks

### 1. useFinanceiroStats.ts (~60 linhas)
```typescript
export function useFinanceiroStats() {
  const [stats, setStats] = useState<FinanceiroStats | null>(null);
  const [loading, setLoading] = useState(true);
  
  const loadStats = async () => {
    // Buscar estatísticas da API
  };
  
  return { stats, loading, reload: loadStats };
}
```

### 2. useAssinaturas.ts (~80 linhas)
```typescript
export function useAssinaturas() {
  const [assinaturas, setAssinaturas] = useState<Assinatura[]>([]);
  const [loading, setLoading] = useState(true);
  
  const loadAssinaturas = async () => {
    // Buscar assinaturas (Asaas + Mercado Pago)
  };
  
  return { assinaturas, loading, reload: loadAssinaturas };
}
```

### 3. usePagamentos.ts (~100 linhas)
```typescript
export function usePagamentos() {
  const [pagamentos, setPagamentos] = useState<Pagamento[]>([]);
  const [filtroStatus, setFiltroStatus] = useState('todos');
  const [loading, setLoading] = useState(true);
  
  const loadPagamentos = async () => {
    // Buscar pagamentos
  };
  
  const pagamentosFiltrados = useMemo(() => {
    // Filtrar por status
  }, [pagamentos, filtroStatus]);
  
  return {
    pagamentos,
    pagamentosFiltrados,
    filtroStatus,
    setFiltroStatus,
    loading,
    reload: loadPagamentos
  };
}
```

### 4. useAsaasActions.ts (~120 linhas)
```typescript
export function useAsaasActions() {
  const [gerandoCobranca, setGerandoCobranca] = useState<number | null>(null);
  
  const downloadBoleto = async (payment: Pagamento) => {
    // Baixar boleto Asaas
  };
  
  const updateStatus = async (paymentId: number) => {
    // Atualizar status no Asaas
  };
  
  const createManualPayment = async (assinaturaId: number, dueDate?: string) => {
    // Criar cobrança manual
  };
  
  const deletePayment = async (paymentId: number) => {
    // Excluir cobrança
  };
  
  return {
    downloadBoleto,
    updateStatus,
    createManualPayment,
    deletePayment,
    gerandoCobranca
  };
}
```

### 5. useMercadoPagoActions.ts (~100 linhas)
```typescript
export function useMercadoPagoActions() {
  const [gerandoPix, setGerandoPix] = useState<number | null>(null);
  const [atualizandoMP, setAtualizandoMP] = useState<string | null>(null);
  
  const downloadBoleto = async (payment: Pagamento) => {
    // Buscar URL do boleto via API
  };
  
  const gerarPix = async (payment: Pagamento) => {
    // Gerar PIX para pagamento
  };
  
  const updateStatus = async (lojaSlug: string) => {
    // Sincronizar com API Mercado Pago
  };
  
  return {
    downloadBoleto,
    gerarPix,
    updateStatus,
    gerandoPix,
    atualizandoMP
  };
}
```

---

## 🎨 Detalhamento dos Componentes

### 1. FinanceiroStats.tsx (~50 linhas)
- Grid com 4 cards de estatísticas
- Receita total, assinaturas ativas, pagamentos pendentes, receita pendente

### 2. AssinaturasTab.tsx (~80 linhas)
- Lista de assinaturas
- Renderiza AssinaturaCard para cada item
- Estado de loading

### 3. AssinaturaCard.tsx (~150 linhas)
- Card individual de assinatura
- Detecta provedor (Asaas ou Mercado Pago)
- Renderiza AssinaturaAsaas ou AssinaturaMercadoPago

### 4. AssinaturaAsaas.tsx (~80 linhas)
- Seção específica para assinaturas Asaas
- Botões: Baixar Boleto, Copiar PIX, Atualizar Status, Nova Cobrança, Excluir

### 5. AssinaturaMercadoPago.tsx (~80 linhas)
- Seção específica para assinaturas Mercado Pago
- Botões: Baixar Boleto, Gerar PIX, Copiar PIX, Atualizar Status

### 6. PagamentosTab.tsx (~60 linhas)
- Container da tab de pagamentos
- Renderiza PagamentosFiltros e PagamentosTable

### 7. PagamentosFiltros.tsx (~40 linhas)
- Botões de filtro por status
- Todos, PENDING, RECEIVED, CONFIRMED, OVERDUE

### 8. PagamentosTable.tsx (~120 linhas)
- Tabela de pagamentos
- Colunas: Cliente, Valor, Status, Vencimento, Ações
- Ações específicas por provedor

---

## 📦 Redução de Código

### Antes
- **Total**: 673 linhas
- **Arquivo único**: Difícil manutenção
- **Componentes inline**: Não reutilizáveis
- **Lógica misturada**: Hard to test

### Depois
- **Página principal**: ~150 linhas
- **Hooks**: ~460 linhas (5 arquivos)
- **Componentes**: ~660 linhas (8 arquivos)
- **Total**: ~1.270 linhas (distribuídas em 14 arquivos)

**Benefícios**:
- Código organizado e modular
- Componentes reutilizáveis
- Lógica separada da UI
- Fácil de testar
- Fácil de manter
- Separação clara Asaas vs Mercado Pago

---

## 🎯 Melhorias de Layout

### 1. Separação Visual Asaas vs Mercado Pago

**Proposta**: Adicionar badge de provedor nos cards
```tsx
<span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
  {provedor === 'asaas' ? '🔵 Asaas' : '🟢 Mercado Pago'}
</span>
```

### 2. Filtros por Provedor

**Proposta**: Adicionar filtro de provedor na tab de assinaturas
```tsx
<select onChange={(e) => setFiltroProvedor(e.target.value)}>
  <option value="todos">Todos</option>
  <option value="asaas">Asaas</option>
  <option value="mercadopago">Mercado Pago</option>
</select>
```

### 3. Estatísticas Separadas

**Proposta**: Mostrar estatísticas por provedor
```tsx
<div className="grid grid-cols-2 gap-4">
  <div>
    <h3>Asaas</h3>
    <p>Receita: R$ X</p>
    <p>Assinaturas: Y</p>
  </div>
  <div>
    <h3>Mercado Pago</h3>
    <p>Receita: R$ X</p>
    <p>Assinaturas: Y</p>
  </div>
</div>
```

### 4. Dark Mode

**Proposta**: Adicionar suporte completo a dark mode em todos os componentes

---

## 🚀 Plano de Execução

### Fase 1: Criar Hooks (1h)
1. useFinanceiroStats.ts
2. useAssinaturas.ts
3. usePagamentos.ts
4. useAsaasActions.ts
5. useMercadoPagoActions.ts

### Fase 2: Criar Componentes (2h)
1. FinanceiroStats.tsx
2. PagamentosFiltros.tsx
3. PagamentosTable.tsx
4. PagamentosTab.tsx
5. AssinaturaAsaas.tsx
6. AssinaturaMercadoPago.tsx
7. AssinaturaCard.tsx (refatorar)
8. AssinaturasTab.tsx

### Fase 3: Refatorar Página Principal (30min)
1. Importar hooks e componentes
2. Orquestrar estado
3. Renderizar componentes

### Fase 4: Melhorias de Layout (30min)
1. Adicionar badges de provedor
2. Adicionar filtros por provedor
3. Melhorar estatísticas
4. Adicionar dark mode

### Fase 5: Testes e Deploy (30min)
1. Testar todas as funcionalidades
2. Verificar dark mode
3. Deploy backend + frontend

**Tempo Total Estimado**: 4-5 horas

---

## ✅ Checklist de Implementação

### Hooks
- [ ] useFinanceiroStats.ts
- [ ] useAssinaturas.ts
- [ ] usePagamentos.ts
- [ ] useAsaasActions.ts
- [ ] useMercadoPagoActions.ts

### Componentes
- [ ] FinanceiroStats.tsx
- [ ] PagamentosFiltros.tsx
- [ ] PagamentosTable.tsx
- [ ] PagamentosTab.tsx
- [ ] AssinaturaAsaas.tsx
- [ ] AssinaturaMercadoPago.tsx
- [ ] AssinaturaCard.tsx (refatorar)
- [ ] AssinaturasTab.tsx
- [ ] index.ts

### Página
- [ ] page.tsx (refatorar)

### Melhorias
- [ ] Badges de provedor
- [ ] Filtros por provedor
- [ ] Estatísticas separadas
- [ ] Dark mode completo

### Testes
- [ ] Testar Asaas
- [ ] Testar Mercado Pago
- [ ] Testar filtros
- [ ] Testar dark mode

### Deploy
- [ ] Commit
- [ ] Deploy frontend
- [ ] Testar em produção

---

**Status**: 📋 Planejamento Concluído  
**Próximo Passo**: Iniciar implementação  
**Versão**: v780
