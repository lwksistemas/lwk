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
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = useCallback(
    async (targetPage: number, append: boolean) => {
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
      setList((prev) => (append ? [...prev, ...result.items] : result.items));
      setHasMore(result.hasMore);
      setTotalCount(result.count);
      setPage(result.page);
      return result;
    },
    [path, queryParams, pageSize, paginate, loja],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchPage(1, false);
    } catch (err) {
      setList([]);
      setHasMore(false);
      setTotalCount(null);
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
    // queryParams é objeto recriado pelo caller quando filtros mudam
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchPage, ...reloadDeps]);

  const loadMore = useCallback(async () => {
    if (!hasMore || loadingMore || loading) return;
    setLoadingMore(true);
    try {
      await fetchPage(page + 1, true);
    } catch {
      // mantém lista atual
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, loading, page, fetchPage]);

  useEffect(() => {
    if (enabled) load();
  }, [load, enabled]);

  return { list, setList, loading, load, loadMore, loadingMore, hasMore, totalCount, error };
}
