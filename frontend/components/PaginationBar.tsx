'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface PaginationBarProps {
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
  itemLabel?: string;
}

/** Barra padrão de paginação: Anterior / Próxima com contador. */
export default function PaginationBar({
  page,
  totalPages,
  totalCount,
  pageSize,
  onPageChange,
  loading = false,
  itemLabel = 'registros',
}: PaginationBarProps) {
  if (totalCount <= pageSize) return null;

  const inicio = (page - 1) * pageSize + 1;
  const fim = Math.min(page * pageSize, totalCount);

  return (
    <div className="flex flex-col gap-2 border-t border-gray-200 dark:border-gray-700 pt-3 mt-1">
      <p className="text-xs text-gray-500 dark:text-gray-400 px-1">
        Role até o final da tabela. Use Anterior / Próxima para ver os demais cadastros.
      </p>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-1 pb-1">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Mostrando {inicio}–{fim} de {totalCount} {itemLabel}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={page <= 1 || loading}
          onClick={() => onPageChange(page - 1)}
          className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
          aria-label="Página anterior"
        >
          <ChevronLeft size={18} aria-hidden />
          Anterior
        </button>
        <span className="text-sm text-gray-600 dark:text-gray-400 px-2 min-w-[5rem] text-center">
          {page} / {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages || loading}
          onClick={() => onPageChange(page + 1)}
          className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
          aria-label="Próxima página"
        >
          Próxima
          <ChevronRight size={18} aria-hidden />
        </button>
      </div>
      </div>
    </div>
  );
}
