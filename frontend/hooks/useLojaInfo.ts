/**
 * Hook customizado para carregar informações detalhadas de uma loja
 */
import { useState } from 'react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';

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
      const response = await apiClient.get<LojaInfo>(`/superadmin/lojas/${lojaId}/info_loja/`);
      setLojaInfo(response.data);
      return true;
    } catch (err) {
      logger.warn('Erro ao carregar informações da loja:', err);
      const errorObj = err && typeof err === 'object' ? (err as Record<string, unknown>) : null;
      const response = errorObj?.response as Record<string, unknown> | undefined;
      const errData = response?.data;
      const errorText =
        (typeof errData === 'object' && errData !== null ? (errData as { error?: string }).error : null) ||
        (typeof errData === 'string' ? errData : null) ||
        'Erro desconhecido';
      const mensagemErro = `Erro ao carregar informações: ${errorText}`;
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
