# Análise de Otimizações - Frontend

## 📊 Código Duplicado Identificado

### 1. **Padrão de Dashboard Loading** 🔴 CRÍTICO

**Duplicação:** Todos os 4 templates de dashboard têm código quase idêntico:

```typescript
// Repetido em: clinica-estetica.tsx, crm-vendas.tsx, restaurante.tsx, servicos.tsx

const [loading, setLoading] = useState(true);
const [loadingAgendamentos, setLoadingAgendamentos] = useState(false);
const [estatisticas, setEstatisticas] = useState<Estatisticas>({...});
const [proximosAgendamentos, setProximosAgendamentos] = useState<Agendamento[]>([]);

const loadDashboard = useCallback(async () => {
  try {
    setLoading(true);
    setLoadingAgendamentos(true);
    const response = await clinicaApiClient.get('/...');
    setEstatisticas(response.data.estatisticas);
    setProximosAgendamentos(response.data.proximos);
  } catch (error) {
    toast.error('Erro ao carregar dashboard');
  } finally {
    setLoading(false);
    setLoadingAgendamentos(false);
  }
}, [toast]);

useEffect(() => {
  loadDashboard();
}, []);
```

**Ocorrências:** 4 arquivos × ~40 linhas = **~160 linhas duplicadas**

---

### 2. **Estados de Modais** 🟡 MÉDIO

**Duplicação:** Cada dashboard tem 6-8 estados de modais:

```typescript
const [showModalAgendamento, setShowModalAgendamento] = useState(false);
const [showModalCliente, setShowModalCliente] = useState(false);
const [showModalProcedimentos, setShowModalProcedimentos] = useState(false);
const [showModalProfissional, setShowModalProfissional] = useState(false);
const [showModalProtocolos, setShowModalProtocolos] = useState(false);
const [showModalAnamnese, setShowModalAnamnese] = useState(false);
const [showModalConfiguracoes, setShowModalConfiguracoes] = useState(false);
const [showModalFuncionarios, setShowModalFuncionarios] = useState(false);
```

**Ocorrências:** 4 arquivos × ~8 estados × 2 linhas = **~64 linhas duplicadas**

---

### 3. **Interface LojaInfo** 🟢 BAIXO

**Duplicação:** Interface idêntica em todos os templates:

```typescript
interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}
```

**Ocorrências:** 4 arquivos × 9 linhas = **~36 linhas duplicadas**

---

### 4. **Constantes de Status** 🟢 BAIXO

**Duplicação:** Arrays de status repetidos:

```typescript
const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado', color: '#3B82F6' },
  { value: 'confirmado', label: 'Confirmado', color: '#10B981' },
  // ...
];
```

**Ocorrências:** Múltiplos arquivos × ~5-10 linhas cada = **~40 linhas duplicadas**

---

## 🎯 Otimizações Propostas

### 1. Criar Hook Customizado `useDashboardData`

**Arquivo:** `frontend/hooks/useDashboardData.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';

interface UseDashboardDataOptions<T, U> {
  endpoint: string;
  initialStats: T;
  initialData: U[];
  transformResponse?: (data: any) => { stats: T; data: U[] };
}

export function useDashboardData<T, U>({
  endpoint,
  initialStats,
  initialData,
  transformResponse
}: UseDashboardDataOptions<T, U>) {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [stats, setStats] = useState<T>(initialStats);
  const [data, setData] = useState<U[]>(initialData);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setLoadingData(true);
      const response = await clinicaApiClient.get(endpoint);
      
      if (transformResponse) {
        const { stats: newStats, data: newData } = transformResponse(response.data);
        setStats(newStats);
        setData(newData);
      } else {
        setStats(response.data.estatisticas || initialStats);
        setData(response.data.proximos || response.data.results || initialData);
      }
    } catch (error) {
      toast.error('Erro ao carregar dados do dashboard');
      console.error('Erro ao carregar dashboard:', error);
    } finally {
      setLoading(false);
      setLoadingData(false);
    }
  }, [endpoint, initialStats, initialData, transformResponse, toast]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    loading,
    loadingData,
    stats,
    data,
    reload: loadDashboard
  };
}
```

**Uso:**
```typescript
// Antes: ~40 linhas
const [loading, setLoading] = useState(true);
const [estatisticas, setEstatisticas] = useState<Estatisticas>({...});
const loadDashboard = useCallback(async () => { ... }, []);
useEffect(() => { loadDashboard(); }, []);

// Depois: ~5 linhas
const { loading, stats, data, reload } = useDashboardData({
  endpoint: '/clinica/agendamentos/dashboard/',
  initialStats: { agendamentos_hoje: 0, ... },
  initialData: []
});
```

**Redução:** ~160 linhas → ~40 linhas = **-120 linhas**

---

### 2. Criar Hook `useModals`

**Arquivo:** `frontend/hooks/useModals.ts`

```typescript
import { useState, useCallback } from 'react';

type ModalState = Record<string, boolean>;

export function useModals<T extends string>(modalNames: T[]) {
  const initialState = modalNames.reduce((acc, name) => {
    acc[name] = false;
    return acc;
  }, {} as Record<T, boolean>);

  const [modals, setModals] = useState<Record<T, boolean>>(initialState);

  const openModal = useCallback((name: T) => {
    setModals(prev => ({ ...prev, [name]: true }));
  }, []);

  const closeModal = useCallback((name: T) => {
    setModals(prev => ({ ...prev, [name]: false }));
  }, []);

  const toggleModal = useCallback((name: T) => {
    setModals(prev => ({ ...prev, [name]: !prev[name] }));
  }, []);

  const closeAll = useCallback(() => {
    setModals(initialState);
  }, [initialState]);

  return {
    modals,
    openModal,
    closeModal,
    toggleModal,
    closeAll
  };
}
```

**Uso:**
```typescript
// Antes: ~16 linhas
const [showModalAgendamento, setShowModalAgendamento] = useState(false);
const [showModalCliente, setShowModalCliente] = useState(false);
const [showModalProcedimentos, setShowModalProcedimentos] = useState(false);
// ... mais 5 modais

// Depois: ~3 linhas
const { modals, openModal, closeModal } = useModals([
  'agendamento', 'cliente', 'procedimentos', 'profissional', 
  'protocolos', 'anamnese', 'configuracoes', 'funcionarios'
]);

// Uso:
<button onClick={() => openModal('agendamento')}>Novo Agendamento</button>
{modals.agendamento && <ModalAgendamento onClose={() => closeModal('agendamento')} />}
```

**Redução:** ~64 linhas → ~12 linhas = **-52 linhas**

---

### 3. Criar Arquivo de Types Compartilhados

**Arquivo:** `frontend/types/dashboard.ts`

```typescript
export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

export interface BaseEstatisticas {
  receita_mensal: number;
}

export interface EstatisticasClinica extends BaseEstatisticas {
  agendamentos_hoje: number;
  agendamentos_mes: number;
  clientes_ativos: number;
  procedimentos_ativos: number;
}

export interface EstatisticasCRM extends BaseEstatisticas {
  leads_ativos: number;
  negociacoes: number;
  vendas_mes: number;
  receita: number;
}

export interface EstatisticasServicos extends BaseEstatisticas {
  agendamentos_hoje: number;
  ordens_abertas: number;
  orcamentos_pendentes: number;
}

export interface EstatisticasRestaurante extends BaseEstatisticas {
  pedidos_hoje: number;
  mesas_ocupadas: string;
  cardapio: number;
  faturamento: number;
}
```

**Redução:** ~36 linhas → ~5 linhas (import) = **-31 linhas**

---

### 4. Criar Arquivo de Constantes

**Arquivo:** `frontend/constants/status.ts`

```typescript
export const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado', color: '#3B82F6' },
  { value: 'confirmado', label: 'Confirmado', color: '#10B981' },
  { value: 'em_andamento', label: 'Em Andamento', color: '#F59E0B' },
  { value: 'concluido', label: 'Concluído', color: '#059669' },
  { value: 'cancelado', label: 'Cancelado', color: '#EF4444' }
] as const;

export const STATUS_OS = [
  { value: 'aberta', label: 'Aberta', color: '#3B82F6' },
  { value: 'em_andamento', label: 'Em Andamento', color: '#F59E0B' },
  { value: 'aguardando_peca', label: 'Aguardando Peça', color: '#8B5CF6' },
  { value: 'concluida', label: 'Concluída', color: '#059669' },
  { value: 'cancelada', label: 'Cancelada', color: '#EF4444' }
] as const;

export const STATUS_LEAD = [
  { value: 'novo', label: 'Novo Lead' },
  { value: 'contato_inicial', label: 'Contato Inicial' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'proposta_enviada', label: 'Proposta Enviada' },
  { value: 'negociacao', label: 'Negociação' },
  { value: 'fechado', label: 'Fechado' },
  { value: 'perdido', label: 'Perdido' }
] as const;

export const ORIGENS_CRM = [
  { value: 'site', label: 'Site' },
  { value: 'indicacao', label: 'Indicação' },
  { value: 'redes_sociais', label: 'Redes Sociais' },
  { value: 'email_marketing', label: 'Email Marketing' },
  { value: 'evento', label: 'Evento' },
  { value: 'telefone', label: 'Telefone' },
  { value: 'outro', label: 'Outro' }
] as const;
```

**Redução:** ~40 linhas → ~5 linhas (import) = **-35 linhas**

---

## 📈 Impacto Total

| Otimização | Linhas Removidas | Linhas Adicionadas | Ganho Líquido |
|------------|------------------|-------------------|---------------|
| useDashboardData hook | ~160 | ~40 | **-120** |
| useModals hook | ~64 | ~12 | **-52** |
| Types compartilhados | ~36 | ~5 | **-31** |
| Constantes compartilhadas | ~40 | ~5 | **-35** |
| **TOTAL** | **~300** | **~62** | **-238** |

---

## 🎯 Plano de Implementação

### Fase 1: Criar Utilitários (30 min)
1. Criar `frontend/hooks/useDashboardData.ts`
2. Criar `frontend/hooks/useModals.ts`
3. Criar `frontend/types/dashboard.ts`
4. Criar `frontend/constants/status.ts`

### Fase 2: Migrar Templates (1-2 horas)
1. Migrar `clinica-estetica.tsx`
2. Migrar `crm-vendas.tsx`
3. Migrar `restaurante.tsx`
4. Migrar `servicos.tsx`

### Fase 3: Testar e Deploy (30 min)
1. Testar localmente cada dashboard
2. Commit e push
3. Deploy automático no Vercel

**Tempo total estimado:** 2-3 horas

---

## ✅ Benefícios

1. **Manutenibilidade:** Correções em 1 lugar
2. **Consistência:** Comportamento idêntico em todos os dashboards
3. **Reusabilidade:** Hooks podem ser usados em novos dashboards
4. **Type Safety:** Types compartilhados garantem consistência
5. **Performance:** Código mais limpo = bundle menor

---

## 📝 Próximos Passos

Após aprovação, implementar na ordem:
1. ✅ Criar hooks e types
2. ✅ Migrar templates
3. ✅ Testar
4. ✅ Deploy
