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

/** Resultado de criar/atualizar/excluir — mensagem imediata sem depender do re-render do `error`. */
export type PlanoMutationResult =
  | { ok: true }
  | { ok: false; message: string };

function parseApiError(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: unknown } };
  const data = e.response?.data;
  if (typeof data === 'string' && data.trim()) return data;
  if (data && typeof data === 'object') {
    const rec = data as Record<string, unknown>;
    if (typeof rec.error === 'string') return rec.error;
    if (typeof rec.detail === 'string') return rec.detail;
    try {
      return JSON.stringify(data);
    } catch {
      return fallback;
    }
  }
  return fallback;
}

export function usePlanoActions() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const criarPlano = async (
    data: PlanoFormData,
    tipoLojaId?: number | null
  ): Promise<PlanoMutationResult> => {
    setLoading(true);
    setError(null);
    try {
      const payload = { ...data } as Record<string, unknown>;
      if (tipoLojaId != null) {
        payload.tipos_loja = [tipoLojaId];
      }
      await apiClient.post('/superadmin/planos/', payload);
      return { ok: true };
    } catch (err: unknown) {
      const errorMsg = parseApiError(err, 'Erro ao criar plano');
      setError(errorMsg);
      return { ok: false, message: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const atualizarPlano = async (id: number, data: PlanoFormData): Promise<PlanoMutationResult> => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.put(`/superadmin/planos/${id}/`, data);
      return { ok: true };
    } catch (err: unknown) {
      const errorMsg = parseApiError(err, 'Erro ao atualizar plano');
      setError(errorMsg);
      return { ok: false, message: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const excluirPlano = async (plano: Plano): Promise<PlanoMutationResult> => {
    if (plano.total_lojas > 0) {
      const msg = 'Não é possível excluir um plano que possui lojas associadas.';
      setError(msg);
      return { ok: false, message: msg };
    }

    setLoading(true);
    setError(null);
    try {
      await apiClient.delete(`/superadmin/planos/${plano.id}/`);
      return { ok: true };
    } catch (err: unknown) {
      const errorMsg = parseApiError(err, 'Erro ao excluir plano');
      setError(errorMsg);
      return { ok: false, message: errorMsg };
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
