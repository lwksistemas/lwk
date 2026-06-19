'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { clearOrphanStorageKeys } from '@/lib/storage-cleanup';

export interface Loja {
  id: number;
  nome: string;
  slug: string;
  cpf_cnpj: string;
  atalho?: string;
  logo?: string;
  tipo_loja_nome: string;
  plano_nome: string;
  owner_username: string;
  owner_email: string;
  owner_full_name?: string;
  owner_telefone?: string;
  senha_provisoria: string;
  is_active: boolean;
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
      const list = Array.isArray(data) ? data : [];
      setLojas(list);
      const slugs = list.flatMap((loja: Loja) =>
        [loja.slug, loja.atalho].filter((s): s is string => Boolean(s))
      );
      clearOrphanStorageKeys(slugs);
    } catch (err: any) {
      const status = err.response?.status;
      const errorMsg =
        status === 401
          ? 'Sessão expirada ou inválida. Faça login novamente no beta.'
          : err.response?.data?.error || err.response?.data?.detail || 'Erro ao carregar lojas';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Erro ao carregar lojas');
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
