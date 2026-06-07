/**
 * Hook para gerenciar listagem e busca de logs
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';

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

function extrairLogsDaResposta(data: unknown, comBuscaTexto: boolean): Log[] {
  if (!data || typeof data !== 'object') return [];

  const body = data as Record<string, unknown>;

  if (comBuscaTexto) {
    if (Array.isArray(body.resultados)) return body.resultados as Log[];
    const paginado = body.results;
    if (paginado && typeof paginado === 'object' && !Array.isArray(paginado)) {
      const nested = (paginado as Record<string, unknown>).resultados;
      if (Array.isArray(nested)) return nested as Log[];
    }
  }

  if (Array.isArray(body.results)) return body.results as Log[];
  if (Array.isArray(body)) return body as Log[];
  return [];
}

export function useLogsList() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(false);
  const [filtros, setFiltros] = useState<FiltrosBusca>({});

  const buscarComFiltros = useCallback(async (filtrosAtivos: FiltrosBusca) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filtrosAtivos).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const endpoint = filtrosAtivos.q
        ? `/superadmin/historico-acessos/busca_avancada/?${params}`
        : `/superadmin/historico-acessos/?${params}`;

      const response = await apiClient.get(endpoint);
      setLogs(extrairLogsDaResposta(response.data, Boolean(filtrosAtivos.q)));
    } catch (error) {
      logger.warn('Erro ao buscar logs:', error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const buscarLogs = useCallback(async () => {
    await buscarComFiltros(filtros);
  }, [filtros, buscarComFiltros]);

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
    buscarComFiltros,
    limparFiltros
  };
}
