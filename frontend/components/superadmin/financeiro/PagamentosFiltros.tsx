/**
 * Componente de filtros de pagamentos
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */

interface PagamentosFiltrosProps {
  filtroStatus: string;
  setFiltroStatus: (status: string) => void;
}

const STATUS_OPTIONS = [
  { value: 'todos', label: 'Todos' },
  { value: 'PENDING', label: 'Pendente' },
  { value: 'RECEIVED', label: 'Recebido' },
  { value: 'CONFIRMED', label: 'Confirmado' },
  { value: 'OVERDUE', label: 'Vencido' }
];

export function PagamentosFiltros({ filtroStatus, setFiltroStatus }: PagamentosFiltrosProps) {
  return (
    <div className="mb-4 flex items-center space-x-4">
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Filtrar por status:
      </span>
      <div className="flex flex-wrap gap-2">
        {STATUS_OPTIONS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setFiltroStatus(value)}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              filtroStatus === value
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
