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

export async function loadClinicaBelezaListPage<T>({
  path,
  page = 1,
  pageSize = CLINICA_BELEZA_PAGE_SIZE,
  fetchOffline,
  saveOffline,
  paginate = true,
}: {
  path: string;
  page?: number;
  pageSize?: number;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
  paginate?: boolean;
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
  const url = paginate
    ? buildClinicaBelezaListUrl(path, { page, page_size: pageSize })
    : path;
  const res = await clinicaBelezaFetch(url);
  const data = await res.json();
  if (!res.ok) {
    return {
      items: [],
      count: 0,
      page: 1,
      pageSize,
      totalPages: 1,
      hasMore: false,
    };
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
}: {
  path: string;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
  reloadDeps?: unknown[];
  paginate?: boolean;
  pageSize?: number;
}) {
  const [list, setList] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [totalCount, setTotalCount] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await loadClinicaBelezaListPage<T>({
        path,
        page: 1,
        pageSize,
        fetchOffline,
        saveOffline,
        paginate,
      });
      setList(result.items);
      setHasMore(result.hasMore);
      setTotalCount(result.count);
      setPage(1);
    } catch {
      setList([]);
      setHasMore(false);
      setTotalCount(null);
      setPage(1);
    } finally {
      setLoading(false);
    }
    // fetchOffline/saveOffline são imports estáveis do módulo
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, pageSize, paginate, ...reloadDeps]);

  const loadMore = useCallback(async () => {
    if (!paginate || !hasMore || loadingMore || loading || isBrowserOffline()) return;
    setLoadingMore(true);
    try {
      const result = await loadClinicaBelezaListPage<T>({
        path,
        page: page + 1,
        pageSize,
        fetchOffline,
        saveOffline,
        paginate: true,
      });
      setList((prev) => [...prev, ...result.items]);
      setHasMore(result.hasMore);
      setTotalCount(result.count);
      setPage(result.page);
    } catch {
      // mantém lista atual
    } finally {
      setLoadingMore(false);
    }
  }, [paginate, hasMore, loadingMore, loading, page, path, pageSize, fetchOffline, saveOffline]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const onSyncDone = () => {
      if (!isBrowserOffline()) setTimeout(() => load(), 500);
    };
    window.addEventListener('offline-sync-done', onSyncDone);
    return () => window.removeEventListener('offline-sync-done', onSyncDone);
  }, [load]);

  return { list, setList, loading, load, loadMore, loadingMore, hasMore, totalCount };
}

/** Entidades sem cache offline (campanhas, protocolos, etc.). */
export const CLINICA_BELEZA_ONLINE_ONLY = {
  fetchOffline: async (): Promise<unknown[]> => [],
  saveOffline: async (): Promise<void> => {},
};

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
