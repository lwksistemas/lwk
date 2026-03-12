'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import apiClient from '@/lib/api-client';

interface CRMConfig {
  id: number;
  origens_leads: Array<{ key: string; label: string; ativo: boolean }>;
  etapas_pipeline: any[];
  colunas_leads: string[];
  modulos_ativos: Record<string, boolean>;
}

interface CRMConfigContextType {
  config: CRMConfig | null;
  loading: boolean;
  recarregar: () => Promise<void>;
  moduloAtivo: (modulo: string) => boolean;
}

const CRMConfigContext = createContext<CRMConfigContextType | undefined>(undefined);

export function CRMConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<CRMConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const carregarConfig = async () => {
    try {
      const res = await apiClient.get<CRMConfig>('/crm-vendas/config/');
      setConfig(res.data);
    } catch (e) {
      console.error('Erro ao carregar config CRM:', e);
      // Se falhar, usar valores padrão
      setConfig({
        id: 0,
        origens_leads: [],
        etapas_pipeline: [],
        colunas_leads: [],
        modulos_ativos: {
          leads: true,
          contas: true,
          contatos: true,
          pipeline: true,
          atividades: true,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarConfig();
  }, []);

  const moduloAtivo = (modulo: string): boolean => {
    if (!config) return true; // Se não carregou ainda, mostrar tudo
    
    // Módulos principais sempre ativos
    if (['leads', 'pipeline', 'atividades'].includes(modulo)) {
      return true;
    }
    
    return config.modulos_ativos?.[modulo] !== false;
  };

  return (
    <CRMConfigContext.Provider value={{ config, loading, recarregar: carregarConfig, moduloAtivo }}>
      {children}
    </CRMConfigContext.Provider>
  );
}

export function useCRMConfig() {
  const context = useContext(CRMConfigContext);
  if (context === undefined) {
    throw new Error('useCRMConfig deve ser usado dentro de CRMConfigProvider');
  }
  return context;
}
