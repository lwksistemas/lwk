/**
 * Hook para carregar lista de tipos de app
 * ✅ REFATORADO v770: Extraído da página para reutilização
 */
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { TipoApp } from './useTipoAppActions';

export function useTipoAppList() {
  const [tipos, setTipos] = useState<TipoApp[]>([]);
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
      console.error('Erro ao carregar tipos de app:', err);
      setError('Erro ao carregar tipos de app');
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
