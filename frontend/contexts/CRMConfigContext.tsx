'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import apiClient from '@/lib/api-client';

interface CRMConfig {
  id: number;
  origens_leads: Array<{ key: string; label: string; ativo: boolean }>;
  etapas_pipeline: any[];
  colunas_leads: string[];
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
}

const CRMConfigContext = createContext<CRMConfigContextType | undefined>(undefined);

export function CRMConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<CRMConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const carregarConfig = async () => {
    try {
      const res = await apiClient.get<CRMConfig>('/crm-vendas/config/');
      console.log('✅ CRM Config carregado:', res.data);
      setConfig(res.data);
    } catch (e) {
      console.error('❌ Erro ao carregar config CRM:', e);
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
      // Retornar etapas padrão se não carregou ou está vazio
      return [
        { key: 'prospecting', label: 'Prospecção', ordem: 1 },
        { key: 'qualification', label: 'Qualificação', ordem: 2 },
        { key: 'proposal', label: 'Proposta', ordem: 3 },
        { key: 'negotiation', label: 'Negociação', ordem: 4 },
        { key: 'closed_won', label: 'Fechado (ganho)', ordem: 5 },
        { key: 'closed_lost', label: 'Fechado (perdido)', ordem: 6 },
      ];
    }
    
    const ativas = config.etapas_pipeline
      .filter(e => e.ativo)
      .sort((a, b) => a.ordem - b.ordem)
      .map(e => ({ key: e.key, label: e.label, ordem: e.ordem }));
    
    // Se não há etapas ativas, retornar padrão
    if (ativas.length === 0) {
      return [
        { key: 'prospecting', label: 'Prospecção', ordem: 1 },
        { key: 'qualification', label: 'Qualificação', ordem: 2 },
        { key: 'proposal', label: 'Proposta', ordem: 3 },
        { key: 'negotiation', label: 'Negociação', ordem: 4 },
        { key: 'closed_won', label: 'Fechado (ganho)', ordem: 5 },
        { key: 'closed_lost', label: 'Fechado (perdido)', ordem: 6 },
      ];
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

  const colunasLeadsVisiveis = () => {
    // Mapa de labels das colunas
    const labelMap: Record<string, string> = {
      nome: 'Nome',
      empresa: 'Empresa',
      email: 'E-mail',
      telefone: 'Telefone',
      origem: 'Origem',
      status: 'Status',
      valor_estimado: 'Valor Estimado',
      created_at: 'Data de Criação',
    };

    if (!config || !config.colunas_leads || config.colunas_leads.length === 0) {
      // Retornar colunas padrão se não carregou
      const defaultColunas = ['nome', 'empresa', 'telefone', 'email', 'origem', 'status', 'valor_estimado'];
      return defaultColunas.map(key => ({ key, label: labelMap[key] || key }));
    }
    
    return config.colunas_leads.map(key => ({ key, label: labelMap[key] || key }));
  };

  return (
    <CRMConfigContext.Provider value={{ config, loading, recarregar: carregarConfig, moduloAtivo, etapasAtivas, origensAtivas, colunasLeadsVisiveis }}>
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
