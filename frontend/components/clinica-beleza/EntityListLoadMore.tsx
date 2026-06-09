"use client";

import PaginationBar from "@/components/PaginationBar";

interface Props {
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  loading?: boolean;
  onPageChange: (page: number) => void;
  itemLabel?: string;
  /** @deprecated compat — ignorado */
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
  loadedCount?: number;
}

/** Rodapé de listagem clínica — usa paginação Anterior/Próxima padrão do sistema. */
export function EntityListLoadMore({
  page,
  totalPages,
  totalCount,
  pageSize,
  loading,
  onPageChange,
  itemLabel = "registros",
}: Props) {
  return (
    <PaginationBar
      page={page}
      totalPages={totalPages}
      totalCount={totalCount}
      pageSize={pageSize}
      loading={loading}
      onPageChange={onPageChange}
      itemLabel={itemLabel}
    />
  );
}
