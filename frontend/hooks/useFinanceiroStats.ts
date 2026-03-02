/**
 * Hook para gerenciar estatísticas financeiras
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';

export interface FinanceiroStats {
  total_assinaturas: number;
  assinaturas_ativas: number;
  pagamentos_pendentes: number;
  pagamentos_pagos: number;
  pagamentos_vencidos: number;
  receita_total: number;
  receita_pendente: number;
}

export function useFinanceiroStats() {
  const [stats, setStats] = useState<FinanceiroStats | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/superadmin/financeiro-unificado/');
      const data = res.data;
      
      setStats({
        total_assinaturas: data.total_assinaturas ?? 0,
        assinaturas_ativas: data.assinaturas_ativas ?? 0,
        pagamentos_pendentes: data.pagamentos_pendentes ?? 0,
        pagamentos_pagos: data.pagamentos_pagos ?? 0,
        pagamentos_vencidos: data.pagamentos_vencidos ?? 0,
        receita_total: data.receita_total ?? 0,
        receita_pendente: data.receita_pendente ?? 0,
      });
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    stats,
    loading,
    reload: loadStats
  };
}
