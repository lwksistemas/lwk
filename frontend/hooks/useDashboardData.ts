import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';

interface UseDashboardDataOptions<T, U> {
  endpoint: string;
  initialStats: T;
  initialData?: U[];
  transformResponse?: (data: any) => { stats: T; data: U[] };
  enabled?: boolean;
}

interface UseDashboardDataReturn<T, U> {
  loading: boolean;
  loadingData: boolean;
  stats: T;
  data: U[];
  reload: () => Promise<void>;
}

/**
 * Hook customizado para carregar dados do dashboard.
 * Centraliza a lógica de loading, error handling e data fetching.
 * 
 * @example
 * const { loading, stats, data, reload } = useDashboardData({
 *   endpoint: '/clinica/agendamentos/dashboard/',
 *   initialStats: { agendamentos_hoje: 0, receita_mensal: 0 },
 *   initialData: []
 * });
 */
export function useDashboardData<T, U>({
  endpoint,
  initialStats,
  initialData = [] as U[],
  transformResponse,
  enabled = true
}: UseDashboardDataOptions<T, U>): UseDashboardDataReturn<T, U> {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [stats, setStats] = useState<T>(initialStats);
  const [data, setData] = useState<U[]>(initialData);

  const loadDashboard = useCallback(async () => {
    if (!enabled) return;
    
    try {
      setLoading(true);
      setLoadingData(true);
      const response = await clinicaApiClient.get(endpoint);
      
      if (transformResponse) {
        const { stats: newStats, data: newData } = transformResponse(response.data);
        setStats(newStats);
        setData(newData);
      } else {
        // Formato padrão: { estatisticas: {...}, proximos: [...] }
        const responseData = response.data;
        setStats(responseData.estatisticas || responseData || initialStats);
        setData(
          responseData.proximos || 
          responseData.results || 
          (Array.isArray(responseData) ? responseData : initialData)
        );
      }
    } catch (error) {
      toast.error('Erro ao carregar dados do dashboard');
      console.error('Erro ao carregar dashboard:', error);
      setStats(initialStats);
      setData(initialData);
    } finally {
      setLoading(false);
      setLoadingData(false);
    }
  }, [endpoint, initialStats, initialData, transformResponse, toast, enabled]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    loading,
    loadingData,
    stats,
    data,
    reload: loadDashboard
  };
}
