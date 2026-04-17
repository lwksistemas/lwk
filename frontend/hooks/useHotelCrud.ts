import { useCallback, useState } from 'react';
import apiClient from '@/lib/api-client';

interface UseHotelCrudOptions<T> {
  endpoint: string;
}

/**
 * Hook genérico para operações CRUD do módulo Hotel.
 * Elimina duplicação de load/submit/remove entre as páginas.
 */
export function useHotelCrud<T extends { id: number }>({ endpoint }: UseHotelCrudOptions<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.get<T[] | { results?: T[] }>(endpoint);
      const data = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
      setItems(data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail || 'Erro ao carregar dados.');
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  const save = useCallback(async (payload: Record<string, unknown>, editingId?: number) => {
    setSaving(true);
    setError(null);
    try {
      if (editingId) {
        await apiClient.put(`${endpoint}${editingId}/`, payload);
      } else {
        await apiClient.post(endpoint, payload);
      }
      await load();
      return true;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string; [k: string]: unknown } } };
      const detail = err?.response?.data?.detail;
      if (detail) {
        setError(detail);
      } else if (err?.response?.data) {
        const firstError = Object.values(err.response.data).flat()[0];
        setError(typeof firstError === 'string' ? firstError : 'Erro ao salvar.');
      } else {
        setError('Erro ao salvar.');
      }
      return false;
    } finally {
      setSaving(false);
    }
  }, [endpoint, load]);

  const remove = useCallback(async (id: number, label: string) => {
    if (!confirm(`Excluir "${label}"?`)) return false;
    try {
      await apiClient.delete(`${endpoint}${id}/`);
      await load();
      return true;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || 'Erro ao excluir.');
      return false;
    }
  }, [endpoint, load]);

  const postAction = useCallback(async (id: number, action: string) => {
    try {
      await apiClient.post(`${endpoint}${id}/${action}/`);
      await load();
      return true;
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || `Erro na ação ${action}.`);
      return false;
    }
  }, [endpoint, load]);

  return { items, loading, error, saving, setError, load, save, remove, postAction };
}
