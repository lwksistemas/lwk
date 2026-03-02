/**
 * Hook customizado para carregar informações detalhadas de uma loja
 */
import { useState } from 'react';
import apiClient from '@/lib/api-client';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tamanho_banco_mb: number | null;
  tamanho_banco_estimativa_mb: number;
  tamanho_banco_motivo: string | null;
  database_created: boolean;
  espaco_plano_gb: number | null;
  espaco_livre_gb: number | null;
  senha_provisoria: string;
  login_page_url: string;
  owner_username: string;
  owner_email: string;
  owner_telefone?: string;
  storage_usado_mb?: number;
  storage_limite_mb?: number;
  storage_livre_mb?: number;
  storage_livre_gb?: number;
  storage_percentual?: number;
  storage_status?: string;
  storage_status_texto?: string;
  storage_alerta_enviado?: boolean;
  storage_ultima_verificacao?: string | null;
  storage_horas_desde_verificacao?: number | null;
  plano_nome?: string;
}

export function useLojaInfo() {
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLojaInfo = async (lojaId: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    setLojaInfo(null);

    try {
      const response = await apiClient.get(`/superadmin/lojas/${lojaId}/info_loja/`);
      setLojaInfo(response.data);
      return true;
    } catch (err: any) {
      console.error('Erro ao carregar informações da loja:', err);
      const mensagemErro = `Erro ao carregar informações: ${err.response?.data?.error || 'Erro desconhecido'}`;
      setError(mensagemErro);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    lojaInfo,
    loading,
    error,
    loadLojaInfo,
    clearLojaInfo: () => setLojaInfo(null)
  };
}
