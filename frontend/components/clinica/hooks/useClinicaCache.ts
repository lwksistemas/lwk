'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { clinicaApiClient } from '@/lib/api-client';

interface CacheItem<T> {
  data: T;
  timestamp: number;
}

interface UseClinicaCacheOptions {
  ttl?: number; // Time to live em millisegundos (padrão: 5 minutos)
}

// Cache global para persistir entre re-renders
const globalCache = new Map<string, CacheItem<unknown>>();

export function useClinicaCache<T>(
  endpoint: string,
  options: UseClinicaCacheOptions = {}
) {
  const { ttl = 5 * 60 * 1000 } = options; // 5 minutos padrão
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  const fetchData = useCallback(async (forceRefresh = false) => {
    const cacheKey = endpoint;
    const now = Date.now();
    
    // Verificar cache
    if (!forceRefresh) {
      const cached = globalCache.get(cacheKey) as CacheItem<T> | undefined;
      if (cached && (now - cached.timestamp) < ttl) {
        if (isMounted.current) {
          setData(cached.data);
          setLoading(false);
        }
        return cached.data;
      }
    }

    // Buscar dados
    try {
      setLoading(true);
      setError(null);
      const response = await clinicaApiClient.get(endpoint);
      
      // Salvar no cache
      globalCache.set(cacheKey, {
        data: response.data,
        timestamp: now
      });

      if (isMounted.current) {
        setData(response.data);
        setLoading(false);
      }
      
      return response.data;
    } catch (err) {
      console.error(`Erro ao carregar ${endpoint}:`, err);
      if (isMounted.current) {
        setError('Erro ao carregar dados');
        setLoading(false);
      }
      return null;
    }
  }, [endpoint, ttl]);

  // Carregar dados na montagem
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Função para invalidar o cache
  const invalidate = useCallback(() => {
    globalCache.delete(endpoint);
    fetchData(true);
  }, [endpoint, fetchData]);

  // Função para atualizar o cache manualmente
  const updateCache = useCallback((newData: T) => {
    globalCache.set(endpoint, {
      data: newData,
      timestamp: Date.now()
    });
    setData(newData);
  }, [endpoint]);

  return {
    data,
    loading,
    error,
    refetch: () => fetchData(true),
    invalidate,
    updateCache
  };
}

// Hook específico para clientes
export function useClientes() {
  return useClinicaCache<Array<{ id: number; nome: string; telefone: string; email: string }>>('/clinica/clientes/');
}

// Hook específico para profissionais
export function useProfissionais() {
  return useClinicaCache<Array<{ id: number; nome: string; especialidade: string }>>('/clinica/profissionais/');
}

// Hook específico para procedimentos
export function useProcedimentos() {
  return useClinicaCache<Array<{ id: number; nome: string; preco: string; duracao: number }>>('/clinica/procedimentos/');
}

// Hook para pré-carregar dados frequentes
export function usePreloadClinicaData() {
  const clientes = useClientes();
  const profissionais = useProfissionais();
  const procedimentos = useProcedimentos();

  const isLoading = clientes.loading || profissionais.loading || procedimentos.loading;

  return {
    clientes: clientes.data || [],
    profissionais: profissionais.data || [],
    procedimentos: procedimentos.data || [],
    isLoading,
    refetchAll: () => {
      clientes.refetch();
      profissionais.refetch();
      procedimentos.refetch();
    }
  };
}

// Função para limpar todo o cache
export function clearClinicaCache() {
  globalCache.clear();
}
