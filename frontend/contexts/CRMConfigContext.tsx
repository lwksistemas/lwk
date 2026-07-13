'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import {
  COLUNAS_LEADS_DISPONIVEIS,
  COLUNAS_CONTAS_DISPONIVEIS,
  COLUNAS_CONTATOS_DISPONIVEIS,
  DEFAULT_COLUNAS_LEADS,
  DEFAULT_COLUNAS_CONTAS,
  DEFAULT_COLUNAS_CONTATOS,
  colunasVisiveisFromConfig,
} from '@/lib/crm-colunas-config';
import { ETAPAS_PIPELINE_PADRAO } from '@/constants/crm';

interface EtapaPipeline {
  key: string;
  label: string;
  cor?: string;
  ordem?: number;
  ativo?: boolean;
}

interface CRMConfig {
  id: number;
  origens_leads: Array<{ key: string; label: string; ativo: boolean }>;
  etapas_pipeline: EtapaPipeline[];
  colunas_leads: string[];
  colunas_contas: string[];
  colunas_contatos: string[];
  modulos_ativos: Record<string, boolean>;
  // Configurações de NFS-e
  provedor_nf: 'asaas' | 'issnet' | 'nacional' | 'manual';
  provedor_nf_display?: string;
  issnet_usuario: string;
  issnet_senha?: string;
  issnet_certificado: string | null;
  issnet_senha_certificado?: string;
  codigo_servico_municipal: string;
  descricao_servico_padrao: string;
  aliquota_iss: string;
  inscricao_municipal?: string;
  codigo_cnae?: string;
  optante_simples_nacional?: boolean;
  regime_especial_tributacao?: string;
  incentivador_cultural?: boolean;
  item_lista_servico?: string;
  codigo_nbs?: string;
  issnet_serie_rps?: string;
  issnet_ultimo_rps_conhecido?: number | string | null;
  issnet_numero_lote?: number | string | null;
  /** Em RP o WSDL costuma ser o mesmo da produção; ver texto na tela de NF. */
  issnet_ambiente_homologacao?: boolean;
  emitir_nf_automaticamente: boolean;
  asaas_sandbox?: boolean;
  asaas_api_key_configured?: boolean;
  asaas_webhook_url?: string;
  asaas_webhook_token_configured?: boolean;
  asaas_webhook_token_masked?: string;
  asaas_webhook_token_length?: number;
  /** Senhas ISSNet + certificado já salvas no servidor (teste sem redigitar) */
  issnet_senhas_salvas?: boolean;
}

interface CRMConfigContextType {
  config: CRMConfig | null;
  loading: boolean;
  recarregar: () => Promise<void>;
  moduloAtivo: (modulo: string) => boolean;
  etapasAtivas: () => Array<{ key: string; label: string; ordem: number }>;
  origensAtivas: () => Array<{ key: string; label: string }>;
  colunasLeadsVisiveis: () => Array<{ key: string; label: string }>;
  colunasContasVisiveis: () => Array<{ key: string; label: string }>;
  colunasContatosVisiveis: () => Array<{ key: string; label: string }>;
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
      logger.warn('❌ Erro ao carregar config CRM:', e);
      // Se falhar, usar valores padrão
      setConfig({
        id: 0,
        origens_leads: [],
        etapas_pipeline: [],
        colunas_leads: [],
        colunas_contas: [],
        colunas_contatos: [],
        modulos_ativos: {
          leads: true,
          contas: true,
          contatos: true,
          pipeline: true,
          atividades: true,
        },
        provedor_nf: 'asaas',
        issnet_usuario: '',
        issnet_certificado: null,
        codigo_servico_municipal: '1401',
        descricao_servico_padrao: 'Desenvolvimento e licenciamento de software sob demanda',
        aliquota_iss: '2.00',
        emitir_nf_automaticamente: true,
        asaas_sandbox: false,
        asaas_api_key_configured: false,
        issnet_senhas_salvas: false,
        issnet_ambiente_homologacao: false,
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
    if (!config || !config.etapas_pipeline || config.etapas_pipeline.length === 0) {
      return ETAPAS_PIPELINE_PADRAO.map(({ key, label, ordem }) => ({ key, label, ordem }));
    }

    const ativas = config.etapas_pipeline
      .filter((e) => e.ativo)
      .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0))
      .map((e, idx) => ({ key: e.key, label: e.label, ordem: e.ordem ?? idx }));

    if (ativas.length === 0) {
      return ETAPAS_PIPELINE_PADRAO.map(({ key, label, ordem }) => ({ key, label, ordem }));
    }

    return ativas;
  };

  const origensAtivas = () => {
    if (!config || !config.origens_leads || config.origens_leads.length === 0) {
      // Retornar origens padrão se não carregou ou está vazio
      return [
        { key: 'whatsapp', label: 'WhatsApp' },
        { key: 'facebook', label: 'Facebook' },
        { key: 'instagram', label: 'Instagram' },
        { key: 'site', label: 'Site' },
        { key: 'indicacao', label: 'Indicação' },
        { key: 'outro', label: 'Outro' },
      ];
    }
    
    const ativas = config.origens_leads
      .filter(o => o.ativo)
      .map(o => ({ key: o.key, label: o.label }));
    
    // Se não há origens ativas, retornar padrão
    if (ativas.length === 0) {
      return [
        { key: 'whatsapp', label: 'WhatsApp' },
        { key: 'facebook', label: 'Facebook' },
        { key: 'instagram', label: 'Instagram' },
        { key: 'site', label: 'Site' },
        { key: 'indicacao', label: 'Indicação' },
        { key: 'outro', label: 'Outro' },
      ];
    }
    
    return ativas;
  };

  const colunasLeadsVisiveis = () =>
    colunasVisiveisFromConfig(config?.colunas_leads, COLUNAS_LEADS_DISPONIVEIS, DEFAULT_COLUNAS_LEADS);

  const colunasContasVisiveis = () =>
    colunasVisiveisFromConfig(config?.colunas_contas, COLUNAS_CONTAS_DISPONIVEIS, DEFAULT_COLUNAS_CONTAS);

  const colunasContatosVisiveis = () =>
    colunasVisiveisFromConfig(config?.colunas_contatos, COLUNAS_CONTATOS_DISPONIVEIS, DEFAULT_COLUNAS_CONTATOS);

  return (
    <CRMConfigContext.Provider value={{
      config,
      loading,
      recarregar: carregarConfig,
      moduloAtivo,
      etapasAtivas,
      origensAtivas,
      colunasLeadsVisiveis,
      colunasContasVisiveis,
      colunasContatosVisiveis,
    }}>
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
