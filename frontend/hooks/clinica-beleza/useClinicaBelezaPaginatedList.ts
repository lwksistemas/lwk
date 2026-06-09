"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CLINICA_BELEZA_PAGE_SIZE,
  buildClinicaBelezaListUrl,
  clinicaBelezaFetch,
  parseClinicaBelezaPaginatedResponse,
} from "@/lib/clinica-beleza-api";

export function useClinicaBelezaPaginatedList<T>({
  path,
  queryParams,
  pageSize = CLINICA_BELEZA_PAGE_SIZE,
  reloadDeps = [],
  enabled = true,
  paginate = true,
  loja,
}: {
  path: string;
  queryParams?: Record<string, string | number | undefined | null>;
  pageSize?: number;
  reloadDeps?: unknown[];
  enabled?: boolean;
  paginate?: boolean;
  loja?: { id?: number; slug?: string } | null;
}) {
  const [list, setList] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = useCallback(
    async (targetPage: number) => {
      const params: Record<string, string | number | undefined | null> = {
        ...(queryParams ?? {}),
      };
      if (paginate) {
        params.page = targetPage;
        params.page_size = pageSize;
      }
      const url = buildClinicaBelezaListUrl(path, params);
      const res = await clinicaBelezaFetch(url, {}, loja);
      const data = await res.json();
      if (!res.ok) throw data;
      const result = parseClinicaBelezaPaginatedResponse<T>(data, targetPage, pageSize);
      setList(result.items);
      setTotalCount(result.count);
      setTotalPages(result.totalPages);
      setPage(result.page);
      return result;
    },
    [path, queryParams, pageSize, paginate, loja?.id, loja?.slug],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchPage(1);
    } catch (err) {
      setList([]);
      setTotalCount(null);
      setTotalPages(1);
      setPage(1);
      const msg =
        err && typeof err === 'object' && 'error' in err
          ? String((err as { error: string }).error)
          : err && typeof err === 'object' && 'detail' in err
            ? String((err as { detail: string }).detail)
            : 'Não foi possível carregar a lista.';
      setError(msg);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchPage, ...reloadDeps]);

  const goToPage = useCallback(
    async (targetPage: number) => {
      if (targetPage < 1 || targetPage > totalPages || loading) return;
      setLoading(true);
      try {
        await fetchPage(targetPage);
      } catch {
        // mantém lista atual
      } finally {
        setLoading(false);
      }
    },
    [fetchPage, totalPages, loading],
  );

  useEffect(() => {
    if (enabled) load();
  }, [load, enabled]);

  return {
    list,
    setList,
    loading,
    load,
    page,
    setPage: goToPage,
    totalPages,
    totalCount,
    pageSize,
    error,
    /** @deprecated use setPage */
    loadMore: () => goToPage(page + 1),
    loadingMore: false,
    hasMore: page < totalPages,
  };
}
