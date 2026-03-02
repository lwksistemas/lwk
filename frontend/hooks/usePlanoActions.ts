'use client';

import { useState } from 'react';
import apiClient from '@/lib/api-client';

export interface PlanoFormData {
  nome: string;
  slug: string;
  descricao: string;
  preco_mensal: string;
  preco_anual: string;
  max_produtos: number;
  max_usuarios: number;
  max_pedidos_mes: number;
  espaco_storage_gb: number;
  tem_relatorios_avancados: boolean;
  tem_api_acesso: boolean;
  tem_suporte_prioritario: boolean;
  tem_dominio_customizado: boolean;
  tem_whatsapp_integration: boolean;
  is_active: boolean;
  ordem: number;
}

export interface Plano extends PlanoFormData {
  id: number;
  total_lojas: number;
  tipos_loja_nomes: string[];
  created_at: string;
}

export function usePlanoActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const criarPlano = async (data: PlanoFormData, tipoLojaId?: number | null) => {
    setLoading(true);
    setError(null);
    try {
      const payload = { ...data } as Record<string, unknown>;
      if (tipoLojaId != null) {
        payload.tipos_loja = [tipoLojaId];
      }
      await apiClient.post('/superadmin/planos/', payload);
      return true;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || JSON.stringify(err.response?.data) || 'Erro ao criar plano';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const atualizarPlano = async (id: number, data: PlanoFormData) => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.put(`/superadmin/planos/${id}/`, data);
      return true;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || JSON.stringify(err.response?.data) || 'Erro ao atualizar plano';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const excluirPlano = async (plano: Plano) => {
    if (plano.total_lojas > 0) {
      throw new Error('Não é possível excluir um plano que possui lojas associadas.');
    }

    setLoading(true);
    setError(null);
    try {
      await apiClient.delete(`/superadmin/planos/${plano.id}/`);
      return true;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Erro ao excluir plano';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return {
    criarPlano,
    atualizarPlano,
    excluirPlano,
    loading,
    error,
  };
}
