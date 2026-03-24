/**
 * Hook para ações de tipos de app (criar, editar, excluir)
 * ✅ REFATORADO v770: Extraído da página para reutilização
 */
import { useState } from 'react';
import apiClient from '@/lib/api-client';

export interface TipoApp {
  id: number;
  nome: string;
  slug: string;
  descricao: string;
  dashboard_template: string;
  cor_primaria: string;
  cor_secundaria: string;
  tem_produtos: boolean;
  tem_servicos: boolean;
  tem_agendamento: boolean;
  tem_delivery: boolean;
  tem_estoque: boolean;
  is_active: boolean;
  total_lojas: number;
  created_at: string;
}

export interface TipoAppFormData {
  nome: string;
  slug: string;
  descricao: string;
  dashboard_template: string;
  cor_primaria: string;
  cor_secundaria: string;
  tem_produtos: boolean;
  tem_servicos: boolean;
  tem_agendamento: boolean;
  tem_delivery: boolean;
  tem_estoque: boolean;
  is_active: boolean;
}

export function useTipoAppActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const criarTipoApp = async (formData: TipoAppFormData): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await apiClient.post('/superadmin/tipos-loja/', formData);
      return true;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || JSON.stringify(err.response?.data) || 'Erro ao criar tipo de app';
      setError(errorMsg);
      console.error('Erro ao criar tipo de app:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const atualizarTipoApp = async (id: number, formData: TipoAppFormData): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await apiClient.put(`/superadmin/tipos-loja/${id}/`, formData);
      return true;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || JSON.stringify(err.response?.data) || 'Erro ao atualizar tipo de app';
      setError(errorMsg);
      console.error('Erro ao atualizar tipo de app:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const excluirTipoApp = async (tipo: TipoApp): Promise<boolean> => {
    // Validações
    if (tipo.total_lojas > 0) {
      setError('Não é possível excluir um tipo de app que possui lojas associadas.');
      return false;
    }

    if (!confirm(`Tem certeza que deseja excluir o tipo "${tipo.nome}"?`)) {
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      await apiClient.delete(`/superadmin/tipos-loja/${tipo.id}/`);
      return true;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao excluir tipo de app';
      setError(errorMsg);
      console.error('Erro ao excluir tipo de app:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    criarTipoApp,
    atualizarTipoApp,
    excluirTipoApp,
    loading,
    error,
  };
}
