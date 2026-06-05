"use client";

import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

interface Props {
  hasMore: boolean;
  loading?: boolean;
  loadingMore?: boolean;
  onLoadMore: () => void;
  loadedCount: number;
  totalCount?: number | null;
}

export function EntityListLoadMore({
  hasMore,
  loading,
  loadingMore,
  onLoadMore,
  loadedCount,
  totalCount,
}: Props) {
  if (loading || loadedCount === 0) return null;

  const countLabel =
    totalCount != null
      ? `Exibindo ${loadedCount} de ${totalCount}`
      : `${loadedCount} ${loadedCount === 1 ? "item" : "itens"}`;

  if (!hasMore) {
    return (
      <p className="text-center text-xs text-gray-500 dark:text-gray-400 py-4 border-t border-gray-100 dark:border-neutral-700">
        {countLabel}
      </p>
    );
  }

  return (
    <div className="flex flex-col items-center gap-2 py-4 border-t border-gray-100 dark:border-neutral-700">
      <p className="text-xs text-gray-500 dark:text-gray-400">{countLabel}</p>
      <button
        type="button"
        onClick={onLoadMore}
        disabled={loadingMore || loading}
        className="px-5 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50 transition-opacity"
        style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
      >
        {loadingMore ? "Carregando..." : "Carregar mais"}
      </button>
    </div>
  );
}
