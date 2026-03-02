'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

export interface Loja {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  plano_nome: string;
  owner_username: string;
  owner_email: string;
  owner_telefone?: string;
  senha_provisoria: string;
  is_active: boolean;
  is_trial: boolean;
  database_created: boolean;
  login_page_url: string;
  created_at: string;
}

export function useLojaList() {
  const [lojas, setLojas] = useState<Loja[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadLojas = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/superadmin/lojas/');
      const data = response.data.results || response.data;
      setLojas(Array.isArray(data) ? data : []);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao carregar lojas';
      setError(errorMsg);
      setLojas([]);
    } finally {
      setLoading(false);
    }
  };

  const reload = () => {
    loadLojas();
  };

  useEffect(() => {
    loadLojas();
  }, []);

  return {
    lojas,
    loading,
    error,
    reload,
  };
}
