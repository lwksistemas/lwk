/**
 * Helpers CRUD compartilhados — Clínica da Beleza (lista online/offline, save, delete).
 */

import { useCallback, useEffect, useState } from 'react';
import {
  CLINICA_BELEZA_PAGE_SIZE,
  buildClinicaBelezaListUrl,
  clinicaBelezaFetch,
  parseClinicaBelezaListResponse,
  parseClinicaBelezaPaginatedResponse,
  type ClinicaBelezaPaginatedResult,
} from '@/lib/clinica-beleza-api';
import { isBrowserOffline } from '@/lib/clinica-beleza-offline';

export { parseClinicaBelezaListResponse };

/** Entidades sem cache offline (campanhas, protocolos, listas online-only). */
export const CLINICA_BELEZA_ONLINE_ONLY = {
  fetchOffline: async (): Promise<unknown[]> => [],
  saveOffline: async (): Promise<void> => {},
};

export async function loadClinicaBelezaListPage<T>({
  path,
  page = 1,
  pageSize = CLINICA_BELEZA_PAGE_SIZE,
  fetchOffline,
  saveOffline,
  paginate = true,
  queryParams,
  loja,
}: {
  path: string;
  page?: number;
  pageSize?: number;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
  paginate?: boolean;
  queryParams?: Record<string, string | number | undefined | null>;
  loja?: { id?: number; slug?: string } | null;
}): Promise<ClinicaBelezaPaginatedResult<T>> {
  if (isBrowserOffline()) {
    const data = await fetchOffline();
    const arr = Array.isArray(data) ? (data as T[]) : [];
    return {
      items: arr,
      count: arr.length,
      page: 1,
      pageSize: arr.length || pageSize,
      totalPages: 1,
      hasMore: false,
    };
  }
  const params: Record<string, string | number | undefined | null> = {
    ...(queryParams ?? {}),
  };
  if (paginate) {
    params.page = page;
    params.page_size = pageSize;
  }
  const url = paginate || Object.keys(params).length > 0
    ? buildClinicaBelezaListUrl(path, params)
    : path;
  const res = await clinicaBelezaFetch(url, {}, loja);
  const data = await res.json();
  if (!res.ok) {
    throw data;
  }
  const result = parseClinicaBelezaPaginatedResponse<T>(data, page, pageSize);
  if (page === 1) {
    await saveOffline(result.items);
  }
  return result;
}

export async function loadClinicaBelezaList<T>({
  path,
  fetchOffline,
  saveOffline,
  paginate = false,
}: {
  path: string;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
  paginate?: boolean;
}): Promise<T[]> {
  const result = await loadClinicaBelezaListPage<T>({
    path,
    page: 1,
    fetchOffline,
    saveOffline,
    paginate,
  });
  return result.items;
}

export async function saveClinicaBelezaEntity(
  path: string,
  method: 'POST' | 'PUT',
  body: Record<string, unknown>,
): Promise<unknown> {
  const res = await clinicaBelezaFetch(path, {
    method,
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;
  return data;
}

export async function deleteClinicaBelezaEntity(
  path: string,
  fallbackError = 'Erro ao desativar.',
): Promise<void> {
  const res = await clinicaBelezaFetch(path, { method: 'DELETE' });
  if (!res.ok) {
    const d = await res.json().catch(() => ({}));
    throw new Error((d as { error?: string }).error || fallbackError);
  }
}

/** Lista com cache offline + reload automático após sincronização. */
export function useClinicaBelezaEntityList<T>({
  path,
  fetchOffline,
  saveOffline,
  reloadDeps = [],
  paginate = true,
  pageSize = CLINICA_BELEZA_PAGE_SIZE,
  queryParams,
  loja,
  enabled = true,
}: {
  path: string;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
  reloadDeps?: unknown[];
  paginate?: boolean;
  pageSize?: number;
  queryParams?: Record<string, string | number | undefined | null>;
  loja?: { id?: number; slug?: string } | null;
  enabled?: boolean;
}) {
  const [list, setList] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = useCallback(
    async (targetPage: number) => {
      const result = await loadClinicaBelezaListPage<T>({
        path,
        page: targetPage,
        pageSize,
        fetchOffline,
        saveOffline,
        paginate,
        queryParams,
        loja,
      });
      setList(result.items);
      setHasMore(result.hasMore);
      setTotalCount(result.count);
      setTotalPages(result.totalPages);
      setPage(result.page);
      return result;
    },
    [path, pageSize, fetchOffline, saveOffline, paginate, queryParams, loja?.id, loja?.slug],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchPage(1);
    } catch (err) {
      setList([]);
      setHasMore(false);
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
      if (!paginate || targetPage < 1 || targetPage > totalPages || loading) return;
      if (isBrowserOffline()) return;
      setLoading(true);
      try {
        await fetchPage(targetPage);
      } catch {
        // mantém lista atual
      } finally {
        setLoading(false);
      }
    },
    [paginate, totalPages, loading, fetchPage],
  );

  useEffect(() => {
    if (enabled) load();
  }, [load, enabled]);

  useEffect(() => {
    const onSyncDone = () => {
      if (!isBrowserOffline()) setTimeout(() => load(), 500);
    };
    window.addEventListener('offline-sync-done', onSyncDone);
    return () => window.removeEventListener('offline-sync-done', onSyncDone);
  }, [load]);

  return {
    list,
    setList,
    loading,
    load,
    page,
    setPage: goToPage,
    totalPages,
    pageSize,
    loadMore: () => goToPage(page + 1),
    loadingMore: false,
    hasMore,
    totalCount,
    error,
  };
}

/**
 * Lista paginada online (sem cache offline).
 * Usa o mesmo núcleo de `useClinicaBelezaEntityList`.
 */
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
  return useClinicaBelezaEntityList<T>({
    path,
    fetchOffline: CLINICA_BELEZA_ONLINE_ONLY.fetchOffline,
    saveOffline: CLINICA_BELEZA_ONLINE_ONLY.saveOffline,
    reloadDeps,
    paginate,
    pageSize,
    queryParams,
    loja,
    enabled,
  });
}

/**
 * Resolve deep-link ?id=X buscando o registro na API quando ainda não está na lista paginada.
 */
export function useClinicaBelezaEntityDetail<T extends { id: number }>({
  editIdParam,
  isNovo,
  list,
  fetchById,
  onNew,
  onFound,
}: {
  editIdParam: string | null;
  isNovo: boolean;
  list: T[];
  fetchById: (id: number) => Promise<T>;
  onNew: () => void;
  onFound: (entity: T) => void;
}) {
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (isNovo) {
      onNew();
      return;
    }
    if (!editIdParam) return;

    const found = list.find((x) => String(x.id) === editIdParam);
    if (found) {
      onFound(found);
      return;
    }

    let cancelled = false;
    setLoadingDetail(true);
    fetchById(Number(editIdParam))
      .then((entity) => {
        if (!cancelled) onFound(entity);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });
    return () => {
      cancelled = true;
    };
  }, [editIdParam, isNovo, list, fetchById, onNew, onFound]);

  return { loadingDetail };
}

/** Classes CSS compartilhadas em formulários da clínica. */
export const CLINICA_FORM_INPUT =
  'w-full px-3 py-2.5 border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 text-sm';
