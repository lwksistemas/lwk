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
  etapasAtivas: () => Array<{ key: string; label: string; ordem: number }>;
  origensAtivas: () => Array<{ key: string; label: string }>;
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

  const etapasAtivas = () => {
    if (!config || !config.etapas_pipeline) {
      // Retornar etapas padrão se não carregou
      return [
        { key: 'prospecting', label: 'Prospecção', ordem: 1 },
        { key: 'qualification', label: 'Qualificação', ordem: 2 },
        { key: 'proposal', label: 'Proposta', ordem: 3 },
        { key: 'negotiation', label: 'Negociação', ordem: 4 },
        { key: 'closed_won', label: 'Fechado (ganho)', ordem: 5 },
        { key: 'closed_lost', label: 'Fechado (perdido)', ordem: 6 },
      ];
    }
    
    return config.etapas_pipeline
      .filter(e => e.ativo)
      .sort((a, b) => a.ordem - b.ordem)
      .map(e => ({ key: e.key, label: e.label, ordem: e.ordem }));
  };

  const origensAtivas = () => {
    if (!config || !config.origens_leads) {
      // Retornar origens padrão se não carregou
      return [
        { key: 'whatsapp', label: 'WhatsApp' },
        { key: 'facebook', label: 'Facebook' },
        { key: 'instagram', label: 'Instagram' },
        { key: 'site', label: 'Site' },
        { key: 'indicacao', label: 'Indicação' },
        { key: 'outro', label: 'Outro' },
      ];
    }
    
    return config.origens_leads
      .filter(o => o.ativo)
      .map(o => ({ key: o.key, label: o.label }));
  };

  return (
    <CRMConfigContext.Provider value={{ config, loading, recarregar: carregarConfig, moduloAtivo, etapasAtivas, origensAtivas }}>
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
