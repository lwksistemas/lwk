/**
 * Hook para gerenciar listagem e busca de logs
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';

export interface Log {
  id: number;
  usuario_nome: string;
  usuario_email: string;
  loja_nome: string;
  acao: string;
  recurso: string;
  detalhes: string;
  ip_address: string;
  user_agent: string;
  url: string;
  metodo_http: string;
  status_code: number;
  sucesso: boolean;
  created_at: string;
}

export interface FiltrosBusca {
  q?: string;
  data_inicio?: string;
  data_fim?: string;
  loja_nome?: string;
  usuario_email?: string;
  acao?: string;
  sucesso?: string;
}

export function useLogsList() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const [filtros, setFiltros] = useState<FiltrosBusca>({});

  const buscarLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const endpoint = filtros.q 
        ? `/superadmin/historico-acessos/busca_avancada/?${params}`
        : `/superadmin/historico-acessos/?${params}`;

      const response = await apiClient.get(endpoint);
      
      // Busca avançada retorna formato diferente: { resultados: [...] }
      // Busca normal retorna: { results: [...] } ou array direto
      let data;
      if (filtros.q && response.data.resultados) {
        data = response.data.resultados;
      } else if (response.data.results) {
        data = response.data.results;
      } else if (Array.isArray(response.data)) {
        data = response.data;
      } else {
        data = [];
      }
      
      setLogs(data);
    } catch (error) {
      console.error('Erro ao buscar logs:', error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [filtros]);

  const limparFiltros = useCallback(() => {
    setFiltros({});
    setLogs([]);
  }, []);

  return {
    logs,
    loading,
    filtros,
    setFiltros,
    buscarLogs,
    limparFiltros
  };
}
