# Frontend - Otimizações Criadas v341

## ✅ Fase 1 Concluída: Utilitários Criados

### 📁 Arquivos Criados

#### 1. `frontend/hooks/useDashboardData.ts` ✅
**Propósito:** Hook customizado para carregar dados do dashboard

**Funcionalidades:**
- Gerenciamento automático de loading states
- Error handling centralizado
- Suporte a transformação de resposta customizada
- Reload manual de dados
- Type-safe com generics

**Uso:**
```typescript
const { loading, stats, data, reload } = useDashboardData({
  endpoint: '/clinica/agendamentos/dashboard/',
  initialStats: { agendamentos_hoje: 0, receita_mensal: 0 },
  initialData: []
});
```

**Benefício:** Elimina ~40 linhas de código por dashboard

---

#### 2. `frontend/hooks/useModals.ts` ✅
**Propósito:** Hook para gerenciar múltiplos modais

**Funcionalidades:**
- Gerenciamento de estado de múltiplos modais
- Métodos: openModal, closeModal, toggleModal, closeAll, isOpen
- Type-safe com array de nomes de modais
- Performance otimizada com useCallback e useMemo

**Uso:**
```typescript
const { modals, openModal, closeModal } = useModals([
  'agendamento', 'cliente', 'procedimentos'
]);

// Abrir modal
<button onClick={() => openModal('agendamento')}>Novo</button>

// Renderizar modal
{modals.agendamento && <Modal onClose={() => closeModal('agendamento')} />}
```

**Benefício:** Elimina ~16 linhas de código por dashboard

---

#### 3. `frontend/types/dashboard.ts` ✅
**Propósito:** Types compartilhados entre dashboards

**Interfaces criadas:**
- `LojaInfo` - Informações da loja
- `BaseEstatisticas` - Base para estatísticas
- `EstatisticasClinica` - Estatísticas da clínica
- `EstatisticasCRM` - Estatísticas do CRM
- `EstatisticasServicos` - Estatísticas de serviços
- `EstatisticasRestaurante` - Estatísticas do restaurante
- `Agendamento` - Dados de agendamento
- `Lead` - Dados de lead

**Uso:**
```typescript
import { LojaInfo, EstatisticasClinica } from '@/types/dashboard';

interface Props {
  loja: LojaInfo;
}
```

**Benefício:** Elimina ~9 linhas de código por dashboard

---

#### 4. `frontend/constants/status.ts` ✅
**Propósito:** Constantes de status compartilhadas

**Constantes criadas:**
- `STATUS_AGENDAMENTO` - Status de agendamentos
- `STATUS_OS` - Status de ordens de serviço
- `STATUS_LEAD` - Status de leads
- `ORIGENS_CRM` - Origens de leads
- `STATUS_PEDIDO` - Status de pedidos
- `STATUS_MESA` - Status de mesas

**Uso:**
```typescript
import { STATUS_AGENDAMENTO, STATUS_LEAD } from '@/constants/status';

<select>
  {STATUS_AGENDAMENTO.map(s => (
    <option key={s.value} value={s.value}>{s.label}</option>
  ))}
</select>
```

**Benefício:** Elimina ~10 linhas de código por dashboard

---

## 📊 Impacto Esperado (Após Migração)

### Redução de Código por Dashboard

| Item | Antes | Depois | Redução |
|------|-------|--------|---------|
| Loading logic | ~40 linhas | ~5 linhas | -35 linhas |
| Modal states | ~16 linhas | ~3 linhas | -13 linhas |
| Types | ~9 linhas | ~1 linha | -8 linhas |
| Constantes | ~10 linhas | ~1 linha | -9 linhas |
| **Total por dashboard** | **~75 linhas** | **~10 linhas** | **-65 linhas** |

### Redução Total (4 Dashboards)

| Dashboard | Redução Estimada |
|-----------|------------------|
| clinica-estetica.tsx | -65 linhas |
| crm-vendas.tsx | -65 linhas |
| restaurante.tsx | -65 linhas |
| servicos.tsx | -65 linhas |
| **TOTAL** | **-260 linhas** |

---

## 🎯 Próximos Passos

### Fase 2: Migrar Templates (Pendente)

Para aplicar as otimizações, os templates precisam ser migrados para usar os novos hooks e types:

1. **clinica-estetica.tsx**
   - Substituir loading logic por `useDashboardData`
   - Substituir modal states por `useModals`
   - Importar types de `@/types/dashboard`
   - Importar constantes de `@/constants/status`

2. **crm-vendas.tsx**
   - Mesmas mudanças acima

3. **restaurante.tsx**
   - Mesmas mudanças acima

4. **servicos.tsx**
   - Mesmas mudanças acima

---

## 📝 Exemplo de Migração

### Antes (clinica-estetica.tsx)
```typescript
const [loading, setLoading] = useState(true);
const [loadingAgendamentos, setLoadingAgendamentos] = useState(false);
const [estatisticas, setEstatisticas] = useState<Estatisticas>({
  agendamentos_hoje: 0,
  agendamentos_mes: 0,
  clientes_ativos: 0,
  procedimentos_ativos: 0,
  receita_mensal: 0
});
const [proximosAgendamentos, setProximosAgendamentos] = useState<Agendamento[]>([]);

const [showModalAgendamento, setShowModalAgendamento] = useState(false);
const [showModalCliente, setShowModalCliente] = useState(false);
const [showModalProcedimentos, setShowModalProcedimentos] = useState(false);
// ... mais 5 modais

const loadDashboard = useCallback(async () => {
  try {
    setLoading(true);
    setLoadingAgendamentos(true);
    const response = await clinicaApiClient.get('/clinica/agendamentos/dashboard/');
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

### Depois (clinica-estetica.tsx)
```typescript
import { useDashboardData } from '@/hooks/useDashboardData';
import { useModals } from '@/hooks/useModals';
import { LojaInfo, EstatisticasClinica, Agendamento } from '@/types/dashboard';
import { STATUS_AGENDAMENTO } from '@/constants/status';

const { loading, loadingData, stats, data, reload } = useDashboardData<EstatisticasClinica, Agendamento>({
  endpoint: '/clinica/agendamentos/dashboard/',
  initialStats: {
    agendamentos_hoje: 0,
    agendamentos_mes: 0,
    clientes_ativos: 0,
    procedimentos_ativos: 0,
    receita_mensal: 0
  },
  initialData: []
});

const { modals, openModal, closeModal } = useModals([
  'agendamento', 'cliente', 'procedimentos', 'profissional',
  'protocolos', 'anamnese', 'configuracoes', 'funcionarios'
] as const);
```

**Redução:** ~75 linhas → ~10 linhas = **-65 linhas**

---

## ✅ Status Atual

- [x] Hooks criados e testados
- [x] Types definidos
- [x] Constantes centralizadas
- [x] Documentação completa
- [x] Commit realizado
- [ ] Templates migrados (Fase 2)
- [ ] Testes em produção
- [ ] Deploy no Vercel

---

## 🚀 Como Aplicar

### Opção 1: Deploy Automático (Recomendado)
1. Push para o repositório do frontend
2. Vercel fará deploy automático
3. Testar em produção

### Opção 2: Deploy Manual
1. Navegar para pasta frontend: `cd frontend`
2. Instalar dependências: `npm install`
3. Build: `npm run build`
4. Deploy: `vercel --prod`

---

## 📌 Notas Importantes

1. **Compatibilidade:** Hooks são retrocompatíveis
2. **Type Safety:** TypeScript garante uso correto
3. **Performance:** Hooks otimizados com useCallback/useMemo
4. **Manutenibilidade:** Código centralizado facilita manutenção
5. **Reusabilidade:** Hooks podem ser usados em novos dashboards

---

## 🎉 Conclusão

**Fase 1 concluída com sucesso!**

Criados 4 arquivos utilitários que preparam o frontend para otimizações significativas:
- ✅ 2 hooks customizados
- ✅ 1 arquivo de types
- ✅ 1 arquivo de constantes

**Próximo passo:** Migrar os 4 templates de dashboard para usar os novos utilitários e reduzir ~260 linhas de código duplicado.
