import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';

function unwrapList<T>(data: T[] | { results?: T[] }): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

function errorMessage(e: unknown, fallback: string): string {
  const err = e as { response?: { data?: { detail?: string; [k: string]: unknown } } };
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (err?.response?.data) {
    const first = Object.values(err.response.data).flat()[0];
    if (typeof first === 'string') return first;
  }
  return fallback;
}

/** CRUD simples sem paginação (MVP radiologia). */
export function useRadiologiaCrud<T extends { id: number }>(endpoint: string) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get(endpoint);
      setItems(unwrapList(res.data));
    } catch (e) {
      setError(errorMessage(e, 'Erro ao carregar.'));
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = useCallback(
    async (payload: Record<string, unknown>, editingId?: number) => {
      setSaving(true);
      setError(null);
      try {
        if (editingId) await apiClient.put(`${endpoint}${editingId}/`, payload);
        else await apiClient.post(endpoint, payload);
        await load();
        return true;
      } catch (e) {
        setError(errorMessage(e, 'Erro ao salvar.'));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [endpoint, load],
  );

  const remove = useCallback(
    async (id: number, label: string) => {
      if (!confirm(`Excluir "${label}"?`)) return false;
      try {
        await apiClient.delete(`${endpoint}${id}/`);
        await load();
        return true;
      } catch (e) {
        setError(errorMessage(e, 'Erro ao excluir.'));
        return false;
      }
    },
    [endpoint, load],
  );

  return { items, loading, error, saving, setError, load, save, remove };
}
