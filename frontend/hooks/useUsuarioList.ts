'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { Usuario } from './useUsuarioActions';

export function useUsuarioList() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadUsuarios = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<{ results?: Usuario[]; data?: Usuario[] }>('/superadmin/usuarios/');
      const data = response.data.results || response.data;
      setUsuarios(Array.isArray(data) ? data : []);
    } catch (err) {
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorMsg =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro ao carregar usuários';
      setError(errorMsg);
      setUsuarios([]);
    } finally {
      setLoading(false);
    }
  };

  const reload = () => {
    loadUsuarios();
  };

  useEffect(() => {
    loadUsuarios();
  }, []);

  return {
    usuarios,
    loading,
    error,
    reload,
  };
}
