/**
 * Hook para gerenciar lista de pagamentos com filtros
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useState, useCallback, useMemo } from 'react';
import apiClient from '@/lib/api-client';
import type { Pagamento } from './useAssinaturas';

export function usePagamentos() {
  const [pagamentos, setPagamentos] = useState<Pagamento[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroStatus, setFiltroStatus] = useState<string>('todos');

  const loadPagamentos = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/superadmin/financeiro-unificado/');
      const data = res.data;
      setPagamentos(Array.isArray(data.pagamentos) ? data.pagamentos : []);
    } catch (error) {
      console.error('Erro ao carregar pagamentos:', error);
      setPagamentos([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const pagamentosFiltrados = useMemo(() => {
    if (filtroStatus === 'todos') return pagamentos;
    return pagamentos.filter(p => p.status === filtroStatus);
  }, [pagamentos, filtroStatus]);

  return {
    pagamentos,
    pagamentosFiltrados,
    filtroStatus,
    setFiltroStatus,
    loading,
    reload: loadPagamentos
  };
}
