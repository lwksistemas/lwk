# Estrutura de Componentes - Dashboard Clínica v481

## 📦 Hierarquia de Arquivos

```
frontend/
├── app/
│   └── (dashboard)/
│       └── loja/
│           └── [slug]/
│               └── dashboard/
│                   └── templates/
│                       └── clinica-estetica.tsx ⭐ (Dashboard Principal)
│
├── components/
│   ├── ui/
│   │   ├── Modal.tsx (z-index: z-40) ✅
│   │   ├── Toast.tsx
│   │   └── Skeleton.tsx
│   │
│   ├── calendario/
│   │   └── CalendarioAgendamentos.tsx ✅ (Dark mode completo)
│   │
│   └── clinica/
│       ├── modals/
│       │   ├── ModalClientes.tsx ✅ (Dark mode + sem fullScreen)
│       │   ├── ModalProfissionais.tsx ✅ (Sem fullScreen)
│       │   ├── ModalProcedimentos.tsx ✅ (Dark mode + sem fullScreen)
│       │   ├── ModalProtocolos.tsx ✅ (Dark mode + sem fullScreen)
│       │   ├── ModalAnamnese.tsx ✅ (Sem fullScreen)
│       │   ├── ModalFuncionarios.tsx ✅ (Sem fullScreen)
│       │   ├── ModalConfiguracoes.tsx ✅ (Dark mode + sem fullScreen)
│       │   ├── ConfiguracoesModal.tsx ✅ (Sem fullScreen)
│       │   └── ModalFinanceiro.tsx
│       │
│       ├── shared/
│       │   ├── CrudModal.tsx (Base para todos os modais)
│       │   └── FormField.tsx
│       │
│       └── GerenciadorConsultas.tsx ✅ (Dark mode + sem duplicação)
│
├── hooks/
│   ├── useDashboardData.ts
│   └── useModals.ts
│
└── lib/
    ├── api-client.ts
    └── array-helpers.ts
```

---

## 🎯 Componente Principal: clinica-estetica.tsx

### Estrutura do Componente

```typescript
export default function DashboardClinicaEstetica({ loja }: { loja: LojaInfo }) {
  // 1. Hooks
  const router = useRouter();
  const toast = useToast();
  const { modals, openModal, closeModal } = useModals([...]);
  const { loading, stats, data, reload } = useDashboardData<...>({...});

  // 2. Estados
  const [showCalendario, setShowCalendario] = useState(false);
  const [showConsultas, setShowConsultas] = useState(false);

  // 3. Effects
  useEffect(() => {
    // Garantir X-Loja-ID no sessionStorage
  }, [loja?.id]);

  // 4. Handlers
  const handleDeleteAgendamento = async (id: number) => {...};
  const handleStatusChange = async (id: number, status: string) => {...};
  const handleNovoAgendamento = () => setShowCalendario(true);
  // ... outros handlers

  // 5. Renderização Condicional
  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorState />;
  if (showCalendario) return <CalendarioView />;
  if (showConsultas) return <ConsultasView />;

  // 6. Dashboard Principal
  return (
    <div className="space-y-6 sm:space-y-8">
      <AcoesRapidas />
      <Estatisticas />
      <ProximosAgendamentos />
      <Modais />
    </div>
  );
}
```

### Props e Interfaces

```typescript
interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
}

interface EstatisticasClinica {
  agendamentos_hoje: number;
  agendamentos_mes: number;
  clientes_ativos: number;
  procedimentos_ativos: number;
  receita_mensal: number;
}

interface Agendamento {
  id: number;
  cliente_nome: string;
  procedimento_nome: string;
  profissional_nome: string;
  data: string;
  horario: string;
  status: 'confirmado' | 'agendado' | 'cancelado' | 'concluido';
}
```

---

## 🧩 Componentes Internos

### 1. ActionButton (Ações Rápidas)

```typescript
function ActionButton({ 
  onClick, 
  color, 
  icon, 
  label 
}: { 
  onClick: () => void; 
  color: string; 
  icon: string; 
  label: string;
}) {
  return (
    <button 
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl 
                 text-white font-semibold transition-all duration-200 
                 transform hover:scale-105 active:scale-95
                 shadow-md sm:shadow-lg hover:shadow-xl btn-press
                 relative overflow-hidden 
                 min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
    >
      <div className="absolute inset-0 bg-white/0 
                      group-hover:bg-white/10 transition-colors" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2 
                        transform group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <div className="text-[10px] sm:text-xs md:text-sm 
                        leading-tight text-center">
          {label}
        </div>
      </div>
    </button>
  );
}
```

**Características:**
- ✅ Responsivo (3 tamanhos: mobile, tablet, desktop)
- ✅ Efeito hover com escala e brilho
- ✅ Efeito press (active:scale-95)
- ✅ Área de toque adequada (min-h-[70px])
- ✅ Cor customizável por ação

---

### 2. StatCard (Estatísticas)

```typescript
function StatCard({ 
  title, 
  value, 
  icon, 
  cor, 
  trend 
}: { 
  title: string; 
  value: string | number; 
  icon: string; 
  cor: string; 
  trend?: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 md:p-6 
                    rounded-xl shadow-lg hover:shadow-xl 
                    transition-all duration-200 card-hover group">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-gray-500 dark:text-gray-400 
                         text-xs sm:text-sm font-medium truncate">
            {title}
          </h3>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold 
                        mt-1 sm:mt-2 text-gray-900 dark:text-white truncate" 
             style={{ color: cor }}>
            {value}
          </p>
          {trend && (
            <span className="text-[10px] sm:text-xs text-green-500 
                             dark:text-green-400 font-medium mt-1 inline-block">
              {trend} vs mês anterior
            </span>
          )}
        </div>
        <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 
                        rounded-lg sm:rounded-xl flex items-center justify-center 
                        flex-shrink-0 transform group-hover:scale-110 
                        transition-transform duration-200"
             style={{ backgroundColor: `${cor}20` }}>
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}
```

**Características:**
- ✅ Dark mode completo
- ✅ Trend opcional (comparação com mês anterior)
- ✅ Ícone com background colorido (20% opacidade)
- ✅ Hover com escala no ícone
- ✅ Truncate para textos longos

---

### 3. AgendamentoCard (Próximos Agendamentos)

```typescript
function AgendamentoCard({ 
  agendamento, 
  cor, 
  onDelete, 
  onStatusChange 
}: { 
  agendamento: Agendamento; 
  cor: string;
  onDelete?: (id: number) => void;
  onStatusChange?: (id: number, status: string) => void;
}) {
  const [showActions, setShowActions] = useState(false);
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  const statusConfig = {
    confirmado: { 
      bg: 'bg-green-100 dark:bg-green-900/30', 
      text: 'text-green-800 dark:text-green-300', 
      label: 'Confirmado' 
    },
    agendado: { 
      bg: 'bg-blue-100 dark:bg-blue-900/30', 
      text: 'text-blue-800 dark:text-blue-300', 
      label: 'Agendado' 
    },
    cancelado: { 
      bg: 'bg-red-100 dark:bg-red-900/30', 
      text: 'text-red-800 dark:text-red-300', 
      label: 'Cancelado' 
    },
    concluido: { 
      bg: 'bg-purple-100 dark:bg-purple-900/30', 
      text: 'text-purple-800 dark:text-purple-300', 
      label: 'Concluído' 
    },
  };

  return (
    <div 
      className="flex flex-col sm:flex-row sm:items-center justify-between 
                 p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl 
                 hover:bg-gray-100 dark:hover:bg-gray-700 
                 transition-all duration-200 group card-hover 
                 gap-3 sm:gap-4 relative"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false);
        setShowStatusMenu(false);
      }}
    >
      {/* Avatar do Cliente */}
      <div className="flex items-center space-x-3 sm:space-x-4 flex-1 min-w-0">
        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl 
                        flex items-center justify-center text-white 
                        font-bold text-base sm:text-lg flex-shrink-0
                        transform group-hover:scale-105 transition-transform 
                        shadow-md"
             style={{ backgroundColor: cor }}>
          {agendamento.cliente_nome.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white 
                        text-sm sm:text-base truncate">
            {agendamento.cliente_nome}
          </p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">
            {agendamento.procedimento_nome}
          </p>
          <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-500 truncate">
            Prof: {agendamento.profissional_nome}
          </p>
        </div>
      </div>
      
      {/* Data, Hora, Status e Ações */}
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="sm:text-right">
          <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
            {agendamento.horario}
          </p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
            {agendamento.data}
          </p>
        </div>
        
        {/* Status Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowStatusMenu(!showStatusMenu)}
            className={`text-[10px] sm:text-xs px-2 sm:px-3 py-1 
                        rounded-full font-medium whitespace-nowrap 
                        ${status.bg} ${status.text} 
                        hover:opacity-80 transition-opacity`}
          >
            {status.label}
          </button>
          
          {showStatusMenu && (
            <div className="absolute right-0 top-full mt-1 
                            bg-white dark:bg-gray-800 rounded-lg shadow-lg 
                            border border-gray-200 dark:border-gray-700 
                            z-10 min-w-[140px]">
              {Object.entries(statusConfig).map(([key, config]) => (
                <button
                  key={key}
                  onClick={() => onStatusChange?.(agendamento.id, key)}
                  className="w-full text-left px-3 py-2 text-xs 
                             hover:bg-gray-100 dark:hover:bg-gray-700 
                             first:rounded-t-lg last:rounded-b-lg"
                >
                  {config.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Botão Excluir */}
        {(showActions || window.innerWidth < 640) && (
          <button
            onClick={() => {
              if (confirm(`Excluir agendamento de ${agendamento.cliente_nome}?`)) {
                onDelete?.(agendamento.id);
              }
            }}
            className="p-2 bg-red-500 hover:bg-red-600 text-white 
                       rounded-lg transition-colors active:scale-95 flex-shrink-0"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
```

**Características:**
- ✅ Botão excluir aparece no hover (desktop) ou sempre visível (mobile)
- ✅ Status clicável com dropdown de opções
- ✅ Confirmação antes de excluir
- ✅ Avatar com inicial do cliente
- ✅ Dark mode completo
- ✅ Responsivo e touch-friendly

---

### 4. EmptyState (Estado Vazio)

```typescript
function EmptyState({ 
  message, 
  subMessage, 
  actionLabel, 
  onAction, 
  cor 
}: { 
  message: string; 
  subMessage: string; 
  actionLabel: string; 
  onAction: () => void; 
  cor: string;
}) {
  return (
    <div className="text-center py-8 sm:py-12 px-4">
      <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 
                      rounded-full bg-gray-100 dark:bg-gray-700 
                      flex items-center justify-center">
        <span className="text-2xl sm:text-3xl">📅</span>
      </div>
      <p className="text-base sm:text-lg mb-1 sm:mb-2 
                    text-gray-700 dark:text-gray-300">
        {message}
      </p>
      <p className="text-xs sm:text-sm mb-4 
                    text-gray-500 dark:text-gray-500">
        {subMessage}
      </p>
      <button
        onClick={onAction}
        className="px-4 sm:px-6 py-2.5 sm:py-3 min-h-[44px] 
                   rounded-xl text-white hover:opacity-90 
                   transition-all btn-press shadow-lg 
                   text-sm sm:text-base active:scale-95"
        style={{ backgroundColor: cor }}
      >
        {actionLabel}
      </button>
    </div>
  );
}
```

**Características:**
- ✅ Ícone grande e amigável
- ✅ Mensagem clara e ação sugerida
- ✅ Botão com cor da loja
- ✅ Dark mode completo

---

## 🔄 Lazy Loading de Modais

```typescript
// Importações lazy
const ModalClientes = lazy(() => 
  import('@/components/clinica/modals/ModalClientes')
    .then(m => ({ default: m.ModalClientes }))
);

// Componente de loading
function ModalLoadingFallback() {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm 
                    flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-blue-500 
                          border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-700 dark:text-gray-300">
            Carregando...
          </span>
        </div>
      </div>
    </div>
  );
}

// Uso com Suspense
<Suspense fallback={<ModalLoadingFallback />}>
  {modals.cliente && (
    <ModalClientes 
      loja={loja}
      onClose={() => closeModal('cliente')}
      onSuccess={() => {
        reload();
        toast.success('Cliente salvo com sucesso!');
      }}
    />
  )}
</Suspense>
```

**Benefícios:**
- ✅ Carregamento inicial mais rápido
- ✅ Modais carregados apenas quando necessário
- ✅ Melhor performance geral
- ✅ Loading state durante carregamento

---

## 📝 Resumo

Este documento detalha a estrutura completa de componentes do dashboard da clínica de estética, incluindo:
- Hierarquia de arquivos
- Componente principal e sua estrutura
- Componentes internos (ActionButton, StatCard, AgendamentoCard, EmptyState)
- Sistema de lazy loading
- Props e interfaces TypeScript

Todos os componentes seguem as boas práticas estabelecidas e estão prontos para serem usados como template padrão.
