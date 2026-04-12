'use client';

export interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  vendedor?: number | null;
  vendedor_nome?: string;
  data_fechamento_ganho?: string | null;
  data_fechamento_perdido?: string | null;
  valor_comissao?: string | null;
  /** Usado no filtro por período (criação da oportunidade) */
  created_at?: string;
}

interface Etapa {
  key: string;
  label: string;
  ordem: number;
}

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
  etapas?: Etapa[];
  onCardClick?: (oportunidade: Oportunidade) => void;
  /** Quadro (Kanban) ou lista tabular */
  viewMode?: 'board' | 'list';
  /** Chave da etapa para filtrar; vazio = todas */
  filtroEtapa?: string;
}

function labelEtapa(etapas: Etapa[], key: string): string {
  return etapas.find((e) => e.key === key)?.label ?? key;
}

export default function PipelineBoard({
  oportunidades,
  loading,
  etapas,
  onCardClick,
  viewMode = 'board',
  filtroEtapa = '',
}: PipelineBoardProps) {
  // Etapas padrão se não fornecidas
  const ETAPAS_DEFAULT = [
    { key: 'prospecting', label: 'Prospecção', ordem: 1 },
    { key: 'qualification', label: 'Qualificação', ordem: 2 },
    { key: 'proposal', label: 'Proposta', ordem: 3 },
    { key: 'negotiation', label: 'Negociação', ordem: 4 },
    { key: 'closed_won', label: 'Fechado ganho', ordem: 5 },
    { key: 'closed_lost', label: 'Fechado perdido', ordem: 6 },
  ];
  
  const etapasVisiveis = etapas || ETAPAS_DEFAULT;
  const colunasBoard =
    filtroEtapa.trim() !== ''
      ? etapasVisiveis.filter((e) => e.key === filtroEtapa)
      : etapasVisiveis;

  const oportunidadesLista =
    filtroEtapa.trim() !== ''
      ? oportunidades.filter((o) => o.etapa === filtroEtapa)
      : oportunidades;

  const byEtapa = colunasBoard.map((e) => ({
    ...e,
    items: oportunidades.filter((o) => o.etapa === e.key),
  }));

  if (loading) {
    if (viewMode === 'list') {
      return (
        <div className="rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden animate-pulse">
          <div className="h-10 bg-gray-200 dark:bg-gray-600" />
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-100 dark:bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      );
    }
    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {colunasBoard.map((e) => (
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

  if (viewMode === 'list') {
    const sorted = [...oportunidadesLista].sort((a, b) => {
      const la = labelEtapa(etapasVisiveis, a.etapa);
      const lb = labelEtapa(etapasVisiveis, b.etapa);
      if (la !== lb) return la.localeCompare(lb, 'pt-BR');
      return a.titulo.localeCompare(b.titulo, 'pt-BR');
    });
    return (
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-600">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/80 border-b border-gray-200 dark:border-gray-600 text-left">
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Etapa</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Título</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Lead</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200 text-right">Valor</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Vendedor</th>
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                  Nenhuma oportunidade neste filtro.
                </td>
              </tr>
            ) : (
              sorted.map((o) => (
                <tr
                  key={o.id}
                  className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                  onClick={() => onCardClick?.(o)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onCardClick?.(o);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <td className="px-4 py-3 text-gray-700 dark:text-gray-300 whitespace-nowrap">
                    {labelEtapa(etapasVisiveis, o.etapa)}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{o.titulo}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{o.lead_nome}</td>
                  <td className="px-4 py-3 text-right font-semibold text-green-600 dark:text-green-400 whitespace-nowrap">
                    {formatMoney(o.valor)}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {o.vendedor_nome ?? '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
