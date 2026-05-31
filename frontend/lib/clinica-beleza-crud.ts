/**
 * Helpers CRUD compartilhados — Clínica da Beleza (lista online/offline, save, delete).
 */

import { useCallback, useEffect, useState } from 'react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { isBrowserOffline } from '@/lib/clinica-beleza-offline';

export async function loadClinicaBelezaList<T>({
  path,
  fetchOffline,
  saveOffline,
}: {
  path: string;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
}): Promise<T[]> {
  if (isBrowserOffline()) {
    const data = await fetchOffline();
    return Array.isArray(data) ? (data as T[]) : [];
  }
  const res = await clinicaBelezaFetch(path);
  const data = await res.json();
  if (!res.ok) return [];
  const arr = Array.isArray(data) ? (data as T[]) : [];
  await saveOffline(arr);
  return arr;
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
}: {
  path: string;
  fetchOffline: () => Promise<unknown[]>;
  saveOffline: (items: T[]) => Promise<void>;
  reloadDeps?: unknown[];
}) {
  const [list, setList] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const arr = await loadClinicaBelezaList<T>({ path, fetchOffline, saveOffline });
      setList(arr);
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
    // fetchOffline/saveOffline são imports estáveis do módulo
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...reloadDeps]);

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

  return { list, setList, loading, load };
}

/** Entidades sem cache offline (campanhas, protocolos, etc.). */
export const CLINICA_BELEZA_ONLINE_ONLY = {
  fetchOffline: async (): Promise<unknown[]> => [],
  saveOffline: async (): Promise<void> => {},
};

/** Classes CSS compartilhadas em formulários da clínica. */
export const CLINICA_FORM_INPUT =
  'w-full px-3 py-2.5 border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 text-sm';
