'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
  const pedido = useRef(0);

  useEffect(() => {
    setPage(1);
  }, [paramsKey, path]);

  const aplicarPagina = useCallback((data: { results: T[]; count: number; totalPages: number }) => {
    pedido.current += 1;
    setItems(data.results);
    setTotalCount(data.count);
    setTotalPages(data.totalPages);
    setError(null);
    setLoading(false);
  }, []);

  const reload = useCallback(
    async (
      silent = false,
      overrides?: {
        page?: number;
        params?: Record<string, string | number | undefined | null>;
      },
    ) => {
      if (!enabled) return;
      const id = ++pedido.current;
      if (!silent) setLoading(true);
      try {
        const pageToLoad = overrides?.page ?? page;
        let paramsToLoad = queryParams;
        if (overrides?.params) {
          const cleaned: Record<string, string | number> = {};
          for (const [key, value] of Object.entries(overrides.params)) {
            if (value !== undefined && value !== null && value !== '') {
              cleaned[key] = value;
            }
          }
          paramsToLoad = cleaned;
        }
        const data = await fetchCrmPaginatedPage<T>(path, pageToLoad, pageSize, paramsToLoad);
        if (id !== pedido.current) return;
        setItems(data.results);
        setTotalCount(data.count);
        setTotalPages(data.totalPages);
        setError(null);
      } catch (err) {
        if (id !== pedido.current) return;
        setError(getCrmApiErrorDetail(err, options?.errorFallback ?? 'Erro ao carregar lista.'));
      } finally {
        if (id === pedido.current && !silent) setLoading(false);
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
    aplicarPagina,
  };
}
