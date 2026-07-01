'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { ArrowRight, LucideIcon } from 'lucide-react';

export interface CrmDocumentoStatusFiltroOption {
  value: string;
  label: string;
}

interface CrmDocumentoListPageShellProps {
  titulo: string;
  subtitulo: string;
  slug: string;
  error?: string | null;
  headerActions?: ReactNode;
  filtroStatus: string;
  onFiltroChange: (status: string) => void;
  filtroOpcoes: CrmDocumentoStatusFiltroOption[];
  children: ReactNode;
}

export function CrmDocumentoListPageShell({
  titulo,
  subtitulo,
  error,
  headerActions,
  filtroStatus,
  onFiltroChange,
  filtroOpcoes,
  children,
}: CrmDocumentoListPageShellProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{titulo}</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{subtitulo}</p>
        </div>
        {headerActions && <div className="flex gap-2">{headerActions}</div>}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-[#16325c] rounded-lg shadow border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-[#0d1f3c] flex items-center gap-3 flex-wrap">
          <span className="text-xs text-gray-500 dark:text-gray-400">Filtrar:</span>
          {filtroOpcoes.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onFiltroChange(opt.value)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium transition ${
                filtroStatus === opt.value
                  ? 'bg-[#0176d3] text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {children}
      </div>
    </div>
  );
}

interface CrmDocumentoEmptyStateProps {
  icon: LucideIcon;
  titulo: string;
  subtitulo: string;
  slug: string;
  pipelineLabel?: string;
}

export function CrmDocumentoEmptyState({
  icon: Icon,
  titulo,
  subtitulo,
  slug,
  pipelineLabel = 'Ir para Pipeline',
}: CrmDocumentoEmptyStateProps) {
  return (
    <td colSpan={99} className="py-12 text-center text-gray-500 dark:text-gray-400">
      <Icon size={48} className="mx-auto mb-3 opacity-30" />
      <p className="font-medium">{titulo}</p>
      <p className="text-sm mt-1">{subtitulo}</p>
      <Link
        href={`/loja/${slug}/crm-vendas/pipeline`}
        className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg text-sm"
      >
        {pipelineLabel}
        <ArrowRight size={16} />
      </Link>
    </td>
  );
}
