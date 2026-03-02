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
      const response = await apiClient.get(`/superadmin/planos/por_tipo/?tipo_id=${tipoLojaId}`);
      setPlanos(response.data);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao carregar planos';
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
