export type NFSeProvedor = 'asaas' | 'issnet' | 'nacional' | 'manual';

export interface NFSeFormData {
  provedor_nf: NFSeProvedor;
  issnet_usuario: string;
  issnet_senha: string;
  issnet_senha_certificado: string;
  codigo_servico_municipal: string;
  descricao_servico_padrao: string;
  aliquota_iss: string;
  inscricao_municipal: string;
  codigo_cnae: string;
  optante_simples_nacional: boolean;
  regime_especial_tributacao: string;
  incentivador_cultural: boolean;
  item_lista_servico: string;
  codigo_nbs: string;
  issnet_serie_rps: string;
  issnet_ultimo_rps_conhecido: string;
  issnet_numero_lote: string;
  issnet_ambiente_homologacao: boolean;
  emitir_nf_automaticamente: boolean;
}

export const NFSE_FORM_DEFAULTS: NFSeFormData = {
  provedor_nf: 'asaas',
  issnet_usuario: '',
  issnet_senha: '',
  issnet_senha_certificado: '',
  codigo_servico_municipal: '0601',
  descricao_servico_padrao: 'Serviços de estética, saúde e bem-estar',
  aliquota_iss: '2.00',
  inscricao_municipal: '',
  codigo_cnae: '',
  optante_simples_nacional: true,
  regime_especial_tributacao: '0',
  incentivador_cultural: false,
  item_lista_servico: '',
  codigo_nbs: '',
  issnet_serie_rps: '',
  issnet_ultimo_rps_conhecido: '',
  issnet_numero_lote: '',
  issnet_ambiente_homologacao: false,
  emitir_nf_automaticamente: false,
};

export const NFSE_PROVEDOR_INFO = {
  asaas: {
    titulo: 'Asaas (conta da sua loja)',
    descricao: 'Emissão de NFS-e pela conta Asaas da loja.',
  },
  issnet: {
    titulo: 'ISSNet - Ribeirão Preto (Direto)',
    descricao: 'Emissão direta na Prefeitura com o CNPJ da sua loja. Requer certificado digital A1.',
  },
  nacional: {
    titulo: 'API Nacional NFS-e (Direto)',
    descricao: 'Emissão através da API Nacional NFS-e. Em breve disponível.',
  },
  manual: {
    titulo: 'Emissão Manual',
    descricao: 'Sem integração automática.',
  },
} as const;

export const NFSE_INPUT_CLASS =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white';

export const NFSE_CARD_CLASS =
  'bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6';

export type NFSeBannerMessage = { type: 'success' | 'error'; text: string };
export type NFSeTestMessage = { type: 'ok' | 'error'; text: string };

export interface NFSeConfigSnapshot {
  provedor_nf?: NFSeProvedor;
  issnet_usuario?: string;
  codigo_servico_municipal?: string;
  descricao_servico_padrao?: string;
  aliquota_iss?: string;
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
  issnet_ambiente_homologacao?: boolean;
  emitir_nf_automaticamente?: boolean;
  asaas_sandbox?: boolean;
  asaas_api_key_configured?: boolean;
  asaas_webhook_token_configured?: boolean;
  asaas_webhook_url?: string;
  issnet_certificado?: string | null;
  issnet_senhas_salvas?: boolean;
}

export function nfseFormDataFromConfig(config: NFSeConfigSnapshot): NFSeFormData {
  return {
    provedor_nf: config.provedor_nf || 'asaas',
    issnet_usuario: config.issnet_usuario || '',
    issnet_senha: '',
    issnet_senha_certificado: '',
    codigo_servico_municipal: config.codigo_servico_municipal || '0601',
    descricao_servico_padrao:
      config.descricao_servico_padrao || 'Serviços de estética, saúde e bem-estar',
    aliquota_iss: config.aliquota_iss || '2.00',
    inscricao_municipal: config.inscricao_municipal || '',
    codigo_cnae: config.codigo_cnae || '',
    optante_simples_nacional: config.optante_simples_nacional ?? true,
    regime_especial_tributacao: config.regime_especial_tributacao || '0',
    incentivador_cultural: config.incentivador_cultural ?? false,
    item_lista_servico: config.item_lista_servico || '',
    codigo_nbs: config.codigo_nbs || '',
    issnet_serie_rps: config.issnet_serie_rps || '',
    issnet_ultimo_rps_conhecido:
      config.issnet_ultimo_rps_conhecido != null ? String(config.issnet_ultimo_rps_conhecido) : '',
    issnet_numero_lote: config.issnet_numero_lote != null ? String(config.issnet_numero_lote) : '',
    issnet_ambiente_homologacao: config.issnet_ambiente_homologacao ?? false,
    emitir_nf_automaticamente: config.emitir_nf_automaticamente ?? false,
  };
}
