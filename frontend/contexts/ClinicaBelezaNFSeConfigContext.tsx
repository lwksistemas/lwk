'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';

interface ClinicaNFSeConfig {
  id: number;
  provedor_nf: 'asaas' | 'issnet' | 'nacional' | 'manual';
  provedor_nf_display?: string;
  issnet_usuario: string;
  issnet_senha?: string;
  issnet_certificado: string | null;
  issnet_certificado_nome?: string;
  issnet_senha_certificado?: string;
  issnet_ambiente_homologacao?: boolean;
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
  codigo_servico_municipal: string;
  descricao_servico_padrao: string;
  aliquota_iss: string;
  emitir_nf_automaticamente: boolean;
  asaas_api_key_configured?: boolean;
  asaas_sandbox?: boolean;
  asaas_webhook_url?: string;
  asaas_webhook_token_configured?: boolean;
  issnet_senhas_salvas?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface ClinicaNFSeConfigContextType {
  config: ClinicaNFSeConfig | null;
  loading: boolean;
  recarregar: () => Promise<void>;
}

const ClinicaNFSeConfigContext = createContext<ClinicaNFSeConfigContextType | undefined>(undefined);

export function ClinicaBelezaNFSeConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<ClinicaNFSeConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const carregarConfig = async () => {
    try {
      const res = await apiClient.get<ClinicaNFSeConfig>('/clinica-beleza/nfse-config/');
      setConfig(res.data);
    } catch (e) {
      logger.warn('❌ Erro ao carregar config NFS-e clínica:', e);
      setConfig({
        id: 0,
        provedor_nf: 'asaas',
        issnet_usuario: '',
        issnet_certificado: null,
        codigo_servico_municipal: '0601',
        descricao_servico_padrao: 'Serviços de estética, saúde e bem-estar',
        aliquota_iss: '2.00',
        emitir_nf_automaticamente: true,
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

  return (
    <ClinicaNFSeConfigContext.Provider value={{ config, loading, recarregar: carregarConfig }}>
      {children}
    </ClinicaNFSeConfigContext.Provider>
  );
}

export function useClinicaNFSeConfig() {
  const context = useContext(ClinicaNFSeConfigContext);
  if (context === undefined) {
    throw new Error('useClinicaNFSeConfig deve ser usado dentro de ClinicaBelezaNFSeConfigProvider');
  }
  return context;
}
