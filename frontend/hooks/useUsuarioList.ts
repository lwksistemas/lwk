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
      const response = await apiClient.get('/superadmin/usuarios/');
      const data = response.data.results || response.data;
      setUsuarios(Array.isArray(data) ? data : []);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao carregar usuários';
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
