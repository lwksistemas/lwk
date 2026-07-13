'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchCrmPaginatedPage, getCrmApiErrorDetail } from '@/lib/crm-utils';

export const DEFAULT_PAGE_SIZE = 50;

export function usePaginatedList<T>(
  path: string,
  options?: {
    pageSize?: number;
    params?: Record<string, string | number | undefined | null>;
    enabled?: boolean;
    errorFallback?: string;
  },
) {
  const pageSize = options?.pageSize ?? DEFAULT_PAGE_SIZE;
  const enabled = options?.enabled !== false;
  const paramsKey = useMemo(
    () => JSON.stringify(options?.params ?? {}),
    [options?.params],
  );
  const queryParams = useMemo(() => {
    const raw = options?.params ?? {};
    const cleaned: Record<string, string | number> = {};
    for (const [key, value] of Object.entries(raw)) {
      if (value !== undefined && value !== null && value !== '') {
        cleaned[key] = value;
      }
    }
    return cleaned;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  const [page, setPage] = useState(1);
  const [items, setItems] = useState<T[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPage(1);
  }, [paramsKey, path]);

  const reload = useCallback(
    async (silent = false) => {
      if (!enabled) return;
      if (!silent) setLoading(true);
      try {
        const data = await fetchCrmPaginatedPage<T>(path, page, pageSize, queryParams);
        setItems(data.results);
        setTotalCount(data.count);
        setTotalPages(data.totalPages);
        setError(null);
      } catch (err) {
        setError(getCrmApiErrorDetail(err, options?.errorFallback ?? 'Erro ao carregar lista.'));
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [path, page, pageSize, queryParams, enabled, options?.errorFallback],
  );

  useEffect(() => {
    reload();
  }, [reload]);

  return {
    items,
    setItems,
    page,
    setPage,
    totalCount,
    totalPages,
    pageSize,
    loading,
    error,
    setError,
    reload,
  };
}
