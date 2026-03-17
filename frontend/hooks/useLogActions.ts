/**
 * Hook para ações de logs (exportar, contexto temporal, buscas salvas)
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import { useState, useCallback, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import type { Log, FiltrosBusca } from './useLogsList';

export interface BuscaSalva {
  nome: string;
  filtros: FiltrosBusca;
}

export interface ContextoTemporal {
  antes: Log[];
  depois: Log[];
}

export function useLogActions() {
  const [buscasSalvas, setBuscasSalvas] = useState<BuscaSalva[]>([]);
  const [contextoTemporal, setContextoTemporal] = useState<ContextoTemporal | null>(null);

  // Carregar buscas salvas do localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const salvas = localStorage.getItem('buscas_logs_salvas');
      if (salvas) {
        setBuscasSalvas(JSON.parse(salvas));
      }
    }
  }, []);

  const exportarCSV = useCallback(async (filtros: FiltrosBusca) => {
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await apiClient.get(
        `/superadmin/historico-acessos/exportar/?${params}`,
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `logs_${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erro ao exportar CSV:', error);
    }
  }, []);

  const exportarJSON = useCallback(async (filtros: FiltrosBusca) => {
    try {
      const params = new URLSearchParams();
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });

      const response = await apiClient.get(
        `/superadmin/historico-acessos/exportar_json/?${params}`
      );

      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `logs_${new Date().toISOString()}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erro ao exportar JSON:', error);
    }
  }, []);

  const carregarContextoTemporal = useCallback(async (logId: number) => {
    try {
      const response = await apiClient.get(
        `/superadmin/historico-acessos/${logId}/contexto_temporal/?antes=10&depois=10`
      );
      setContextoTemporal(response.data);
    } catch (error) {
      console.error('Erro ao carregar contexto temporal:', error);
      setContextoTemporal({ antes: [], depois: [] });
    }
  }, []);

  const salvarBusca = useCallback((nome: string, filtros: FiltrosBusca) => {
    if (!nome.trim()) return false;

    const novaBusca: BuscaSalva = {
      nome: nome.trim(),
      filtros: { ...filtros }
    };

    const novasBuscas = [...buscasSalvas, novaBusca];
    setBuscasSalvas(novasBuscas);
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('buscas_logs_salvas', JSON.stringify(novasBuscas));
    }

    return true;
  }, [buscasSalvas]);

  const excluirBusca = useCallback((index: number) => {
    const novasBuscas = buscasSalvas.filter((_, i) => i !== index);
    setBuscasSalvas(novasBuscas);
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('buscas_logs_salvas', JSON.stringify(novasBuscas));
    }
  }, [buscasSalvas]);

  const limparContextoTemporal = useCallback(() => {
    setContextoTemporal(null);
  }, []);

  return {
    buscasSalvas,
    contextoTemporal,
    exportarCSV,
    exportarJSON,
    carregarContextoTemporal,
    limparContextoTemporal,
    salvarBusca,
    excluirBusca
  };
}
