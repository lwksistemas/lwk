'use client';

interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  vendedor_nome?: string;
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
}

export default function PipelineBoard({ oportunidades, loading }: PipelineBoardProps) {
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
            className="w-72 shrink-0 bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 p-4 h-64 animate-pulse"
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
          className="w-72 shrink-0 bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-100 dark:border-gray-700 flex flex-col max-h-[calc(100vh-12rem)]"
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
                <div
                  key={o.id}
                  className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-100 dark:border-gray-600 hover:border-gray-200 dark:hover:border-gray-500 transition-colors"
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
                </div>
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
