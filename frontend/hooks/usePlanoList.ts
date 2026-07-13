'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { Plano } from './usePlanoActions';

export function usePlanoList(tipoId?: number | null) {
  const [planos, setPlanos] = useState<Plano[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPlanos = async (tipoLojaId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<{ results?: Plano[]; data?: Plano[] } | Plano[]>(`/superadmin/planos/por_tipo/?tipo_id=${tipoLojaId}`);
      const raw = response.data;
      const list = Array.isArray(raw) ? raw : Array.isArray((raw as { results?: Plano[] }).results) ? (raw as { results: Plano[] }).results : [];
      setPlanos(list);
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorMsg =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro ao carregar planos';
      setError(errorMsg);
      setPlanos([]);
    } finally {
      setLoading(false);
    }
  };

  const reload = () => {
    if (tipoId) {
      loadPlanos(tipoId);
    }
  };

  useEffect(() => {
    if (tipoId) {
      loadPlanos(tipoId);
    }
  }, [tipoId]);

  return {
    planos,
    loading,
    error,
    loadPlanos,
    reload,
  };
}
