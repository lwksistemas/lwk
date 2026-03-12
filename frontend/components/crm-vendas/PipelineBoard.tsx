'use client';

export interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  vendedor_nome?: string;
  data_fechamento_ganho?: string | null;
  data_fechamento_perdido?: string | null;
  valor_comissao?: string | null;
}

const ETAPAS = [
  { key: 'prospecting', label: 'Prospecção' },
  { key: 'qualification', label: 'Qualificação' },
  { key: 'proposal', label: 'Proposta' },
  { key: 'negotiation', label: 'Negociação' },
  { key: 'closed_won', label: 'Fechado ganho' },
  { key: 'closed_lost', label: 'Fechado perdido' },
];

function formatMoney(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

interface PipelineBoardProps {
  oportunidades: Oportunidade[];
  loading?: boolean;
  onCardClick?: (oportunidade: Oportunidade) => void;
}

export default function PipelineBoard({ oportunidades, loading, onCardClick }: PipelineBoardProps) {
  const byEtapa = ETAPAS.map((e) => ({
    ...e,
    items: oportunidades.filter((o) => o.etapa === e.key),
  }));

  if (loading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {ETAPAS.map((e) => (
          <div
            key={e.key}
            className="w-72 shrink-0 bg-gray-50 dark:bg-gray-700/50 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 h-64 animate-pulse"
          >
            <div className="h-5 bg-gray-200 dark:bg-gray-600 rounded w-2/3 mb-2" />
            <div className="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {byEtapa.map((col) => (
        <div
          key={col.key}
          className="w-72 shrink-0 bg-gray-50 dark:bg-gray-700/50 rounded-xl shadow-sm border border-gray-200 dark:border-gray-600 flex flex-col max-h-[calc(100vh-14rem)]"
        >
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {col.label}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {col.items.length} oportunidade(s)
            </p>
            <p className="text-sm font-medium text-green-600 dark:text-green-400 mt-1">
              {formatMoney(
                col.items.reduce((s, i) => s + parseFloat(String(i.valor)), 0)
              )}
            </p>
          </div>
          <div className="p-2 flex-1 overflow-y-auto space-y-2">
            {col.items.length === 0 ? (
              <p className="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">
                Nenhuma
              </p>
            ) : (
              col.items.map((o) => (
                <button
                  key={o.id}
                  type="button"
                  onClick={() => onCardClick?.(o)}
                  className="w-full p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-100 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                >
                  <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                    {o.titulo}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {o.lead_nome}
                  </p>
                  <p className="text-sm font-semibold text-green-600 dark:text-green-400 mt-1">
                    {formatMoney(o.valor)}
                  </p>
                  {o.vendedor_nome && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {o.vendedor_nome}
                    </p>
                  )}
                  {o.valor_comissao && (
                    <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                      Comissão: {formatMoney(o.valor_comissao)}
                    </p>
                  )}
                  {o.data_fechamento_ganho && (
                    <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                      Ganho em: {new Date(o.data_fechamento_ganho).toLocaleDateString('pt-BR')}
                    </p>
                  )}
                  {o.data_fechamento_perdido && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                      Perdido em: {new Date(o.data_fechamento_perdido).toLocaleDateString('pt-BR')}
                    </p>
                  )}
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">Clique para editar / fechar venda</p>
                </button>
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
