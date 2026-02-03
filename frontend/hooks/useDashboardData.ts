import { useState, useEffect, useCallback, useRef } from 'react';
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
  error: boolean;
}

/**
 * Hook customizado para carregar dados do dashboard.
 * Centraliza a lógica de loading, error handling e data fetching.
 * Previne loops infinitos com retry limitado.
 * 
 * @example
 * const { loading, stats, data, reload, error } = useDashboardData({
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
  const [error, setError] = useState(false);
  
  // Prevenir loops infinitos
  const retryCount = useRef(0);
  const maxRetries = 3;
  const hasShownError = useRef(false);

  const loadDashboard = useCallback(async () => {
    if (!enabled) return;
    
    // Prevenir retry infinito
    if (retryCount.current >= maxRetries) {
      console.warn('Máximo de tentativas atingido para:', endpoint);
      setLoading(false);
      setLoadingData(false);
      setError(true);
      return;
    }
    
    try {
      setLoading(true);
      setLoadingData(true);
      setError(false);
      
      const response = await clinicaApiClient.get(endpoint);
      
      // Reset retry count on success
      retryCount.current = 0;
      hasShownError.current = false;
      
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
    } catch (err: any) {
      console.error('Erro ao carregar dashboard:', err);
      retryCount.current += 1;
      setError(true);
      
      // Mostrar toast apenas uma vez
      if (!hasShownError.current) {
        hasShownError.current = true;
        
        // Verificar se é erro de autenticação
        if (err.response?.status === 401) {
          toast.error('Sessão expirada. Faça login novamente.');
        } else {
          toast.error('Erro ao carregar dados do dashboard');
        }
      }
      
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
    reload: loadDashboard,
    error
  };
}
