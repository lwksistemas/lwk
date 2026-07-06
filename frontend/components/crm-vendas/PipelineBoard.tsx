'use client';

import { useState } from 'react';
import { ETAPAS_PIPELINE_PADRAO } from '@/constants/crm';
import { formatCrmBrl, rotuloExibicaoOportunidade } from '@/lib/crm-utils';

export interface Oportunidade {
  id: number;
  titulo: string;
  valor: string;
  etapa: string;
  lead_nome: string;
  conta_nome?: string | null;
  empresa_prestadora?: number | null;
  empresa_prestadora_nome?: string | null;
  vendedor?: number | null;
  vendedor_nome?: string;
  data_fechamento?: string | null;
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

interface PipelineBoardProps {
  oportunidades: Oportunidade[];
  loading?: boolean;
  etapas?: Etapa[];
  onCardClick?: (oportunidade: Oportunidade) => void;
  onEtapaChange?: (oportunidade: Oportunidade, novaEtapa: string) => void;
  /** Quadro (Kanban) ou lista tabular */
  viewMode?: 'board' | 'list';
  /** Chave da etapa para filtrar; vazio = todas */
  filtroEtapa?: string;
}

const ETAPAS_FECHADAS = new Set(['closed_won', 'closed_lost']);

export default function PipelineBoard({
  oportunidades,
  loading,
  etapas,
  onCardClick,
  onEtapaChange,
  viewMode = 'board',
  filtroEtapa = '',
}: PipelineBoardProps) {
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);

  const etapasVisiveis = etapas || ETAPAS_PIPELINE_PADRAO.map(({ key, label, ordem }) => ({ key, label, ordem }));
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

  const handleDrop = (etapaKey: string) => {
    setDropTarget(null);
    setDraggingId(null);
    if (draggingId == null) return;
    const opp = oportunidades.find((o) => o.id === draggingId);
    if (!opp || opp.etapa === etapaKey) return;
    if (ETAPAS_FECHADAS.has(etapaKey)) {
      onCardClick?.(opp);
      return;
    }
    onEtapaChange?.(opp, etapaKey);
  };

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
      const da = a.created_at ? new Date(a.created_at).getTime() : 0;
      const db = b.created_at ? new Date(b.created_at).getTime() : 0;
      if (da !== db) return db - da;
      return rotuloExibicaoOportunidade(a).localeCompare(rotuloExibicaoOportunidade(b), 'pt-BR');
    });
    return (
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-600">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800/80 border-b border-gray-200 dark:border-gray-600 text-left">
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Cliente</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Empresa</th>
              <th className="px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Prestadora</th>
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
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{o.lead_nome || rotuloExibicaoOportunidade(o)}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{o.conta_nome || '—'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-sm">
                    {o.empresa_prestadora_nome || (
                      <span className="text-amber-600 dark:text-amber-400">Não definida</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-green-600 dark:text-green-400 whitespace-nowrap">
                    {formatCrmBrl(o.valor)}
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
          className={`w-72 shrink-0 bg-gray-50 dark:bg-gray-700/50 rounded-xl shadow-sm border flex flex-col max-h-[calc(100vh-14rem)] transition-colors ${
            dropTarget === col.key
              ? 'border-blue-400 dark:border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800'
              : 'border-gray-200 dark:border-gray-600'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDropTarget(col.key);
          }}
          onDragLeave={() => {
            if (dropTarget === col.key) setDropTarget(null);
          }}
          onDrop={(e) => {
            e.preventDefault();
            handleDrop(col.key);
          }}
        >
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {col.label}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {col.items.length} oportunidade(s)
            </p>
            <p className="text-sm font-medium text-green-600 dark:text-green-400 mt-1">
              {formatCrmBrl(
                col.items.reduce((s, i) => s + parseFloat(String(i.valor)), 0)
              )}
            </p>
          </div>
          <div className="p-2 flex-1 overflow-y-auto space-y-2">
            {col.items.length === 0 ? (
              <p className="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">
                {draggingId != null ? 'Solte aqui' : 'Nenhuma'}
              </p>
            ) : (
              col.items.map((o) => (
                <button
                  key={o.id}
                  type="button"
                  draggable={!!onEtapaChange}
                  onDragStart={(e) => {
                    setDraggingId(o.id);
                    e.dataTransfer.setData('text/plain', String(o.id));
                    e.dataTransfer.effectAllowed = 'move';
                  }}
                  onDragEnd={() => {
                    setDraggingId(null);
                    setDropTarget(null);
                  }}
                  onClick={() => onCardClick?.(o)}
                  className={`w-full p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-100 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left ${
                    draggingId === o.id ? 'opacity-50' : ''
                  } ${onEtapaChange ? 'cursor-grab active:cursor-grabbing' : ''}`}
                >
                  <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                    {rotuloExibicaoOportunidade(o)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {o.empresa_prestadora_nome || o.lead_nome}
                  </p>
                  <p className="text-sm font-semibold text-green-600 dark:text-green-400 mt-1">
                    {formatCrmBrl(o.valor)}
                  </p>
                  {o.empresa_prestadora_nome && (
                    <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1 truncate">
                      {o.empresa_prestadora_nome}
                    </p>
                  )}
                  {o.vendedor_nome && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {o.vendedor_nome}
                    </p>
                  )}
                  {o.valor_comissao && (
                    <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                      Comissão: {formatCrmBrl(o.valor_comissao)}
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
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    {onEtapaChange ? 'Arraste ou clique para editar' : 'Clique para editar / fechar venda'}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
