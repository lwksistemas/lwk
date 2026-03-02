'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export interface TipoLoja {
  id: number;
  nome: string;
  cor_primaria: string;
}

export function useTipoLojaList() {
  const [tipos, setTipos] = useState<TipoLoja[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTipos = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/superadmin/tipos-loja/');
      const data = response.data.results || response.data;
      setTipos(Array.isArray(data) ? data : []);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao carregar tipos';
      setError(errorMsg);
      setTipos([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTipos();
  }, []);

  return {
    tipos,
    loading,
    error,
    reload: loadTipos,
  };
}
