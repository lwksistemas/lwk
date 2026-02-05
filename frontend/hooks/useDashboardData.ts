import { useState, useEffect, useRef } from 'react';
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
 * 
 * ✅ SOLUÇÃO DEFINITIVA: Sem useCallback, executa apenas uma vez no mount
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
  
  // Ref para controlar se o componente está montado
  const isMountedRef = useRef(true);
  const hasLoadedRef = useRef(false);
  const hasShownErrorRef = useRef(false);

  // Função de reload exposta para uso manual
  const reload = useRef(async () => {
    if (!enabled || !isMountedRef.current) return;
    
    try {
      setLoading(true);
      setLoadingData(true);
      setError(false);
      
      const response = await clinicaApiClient.get(endpoint);
      
      if (!isMountedRef.current) return;
      
      hasShownErrorRef.current = false;
      
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
      if (!isMountedRef.current) return;
      
      console.error('Erro ao carregar dashboard:', err);
      setError(true);
      
      // Mostrar toast apenas uma vez
      if (!hasShownErrorRef.current) {
        hasShownErrorRef.current = true;
        
        // Verificar se é erro de autenticação
        if (err.response?.status === 401) {
          toast.error('Sessão expirada. Faça login novamente.');
        } else if (err.response?.status === 429) {
          toast.error('Muitas requisições. Aguarde um momento.');
        } else {
          toast.error('Erro ao carregar dados do dashboard');
        }
      }
      
      setStats(initialStats);
      setData(initialData);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
        setLoadingData(false);
      }
    }
  }).current;

  // Carregar dados apenas uma vez no mount
  useEffect(() => {
    // Sempre carregar se enabled=true, independente de hasLoaded
    // Isso resolve o problema do React Strict Mode (double mount)
    if (!enabled) return;
    
    // Resetar flag se o componente foi remontado
    if (!isMountedRef.current) {
      isMountedRef.current = true;
      hasLoadedRef.current = false;
    }
    
    // Prevenir execução duplicada apenas se já carregou E ainda está montado
    if (hasLoadedRef.current && isMountedRef.current) {
      return;
    }
    
    hasLoadedRef.current = true;
    reload();
    
    // Cleanup: marcar componente como desmontado
    return () => {
      isMountedRef.current = false;
    };
  }, [enabled]); // Depende de enabled para recarregar se mudar

  return {
    loading,
    loadingData,
    stats,
    data,
    reload,
    error
  };
}
