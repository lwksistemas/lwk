import type { ProvedorNf } from "@/lib/nfse-emissao-opcoes";

export type { ProvedorNf };
export type NFSeProvedor = ProvedorNf;

export interface NFSeFormData {
  provedor_nf: NFSeProvedor;
  issnet_usar_padrao_nacional: boolean;
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
  codigo_tributacao_nacional: string;
  codigo_tributacao_municipal: string;
  nacional_codigo_municipio: string;
  indicador_operacao: string;
  cst_ibscbs: string;
  cclass_trib_ibscbs: string;
  p_tot_trib_sn: string;
}

export const NFSE_FORM_DEFAULTS: NFSeFormData = {
  provedor_nf: "asaas",
  issnet_usar_padrao_nacional: true,
  issnet_usuario: "",
  issnet_senha: "",
  issnet_senha_certificado: "",
  codigo_servico_municipal: "0601",
  descricao_servico_padrao: "Serviços de estética, saúde e bem-estar",
  aliquota_iss: "2.00",
  inscricao_municipal: "",
  codigo_cnae: "",
  optante_simples_nacional: true,
  regime_especial_tributacao: "0",
  incentivador_cultural: false,
  item_lista_servico: "",
  codigo_nbs: "",
  issnet_serie_rps: "",
  issnet_ultimo_rps_conhecido: "",
  issnet_numero_lote: "",
  issnet_ambiente_homologacao: false,
  emitir_nf_automaticamente: false,
  codigo_tributacao_nacional: "",
  codigo_tributacao_municipal: "",
  nacional_codigo_municipio: "",
  indicador_operacao: "",
  cst_ibscbs: "",
  cclass_trib_ibscbs: "",
  p_tot_trib_sn: "",
};

export const NFSE_INPUT_CLASS =
  "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white";

export const NFSE_CARD_CLASS =
  "bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6";

export type NFSeBannerMessage = { type: "success" | "error"; text: string };
export type NFSeTestMessage = { type: "ok" | "error"; text: string };

export interface NFSeConfigSnapshot {
  provedor_nf?: NFSeProvedor;
  issnet_usar_padrao_nacional?: boolean;
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
  codigo_tributacao_nacional?: string;
  codigo_tributacao_municipal?: string;
  nacional_codigo_municipio?: string;
  indicador_operacao?: string;
  cst_ibscbs?: string;
  cclass_trib_ibscbs?: string;
  p_tot_trib_sn?: string | number | null;
  asaas_sandbox?: boolean;
  asaas_api_key_configured?: boolean;
  asaas_webhook_token_configured?: boolean;
  asaas_webhook_url?: string;
  issnet_certificado?: string | null;
  issnet_senhas_salvas?: boolean;
}

export function nfseFormDataFromConfig(config: NFSeConfigSnapshot): NFSeFormData {
  return {
    provedor_nf: config.provedor_nf || "asaas",
    issnet_usar_padrao_nacional: config.issnet_usar_padrao_nacional ?? true,
    issnet_usuario: config.issnet_usuario || "",
    issnet_senha: "",
    issnet_senha_certificado: "",
    codigo_servico_municipal: config.codigo_servico_municipal || "0601",
    descricao_servico_padrao:
      config.descricao_servico_padrao || "Serviços de estética, saúde e bem-estar",
    aliquota_iss: config.aliquota_iss || "2.00",
    inscricao_municipal: config.inscricao_municipal || "",
    codigo_cnae: config.codigo_cnae || "",
    optante_simples_nacional: config.optante_simples_nacional ?? true,
    regime_especial_tributacao: config.regime_especial_tributacao || "0",
    incentivador_cultural: config.incentivador_cultural ?? false,
    item_lista_servico: config.item_lista_servico || "",
    codigo_nbs: config.codigo_nbs || "",
    issnet_serie_rps: config.issnet_serie_rps || "",
    issnet_ultimo_rps_conhecido:
      config.issnet_ultimo_rps_conhecido != null ? String(config.issnet_ultimo_rps_conhecido) : "",
    issnet_numero_lote: config.issnet_numero_lote != null ? String(config.issnet_numero_lote) : "",
    issnet_ambiente_homologacao: config.issnet_ambiente_homologacao ?? false,
    emitir_nf_automaticamente: config.emitir_nf_automaticamente ?? false,
    codigo_tributacao_nacional: config.codigo_tributacao_nacional || "",
    codigo_tributacao_municipal: config.codigo_tributacao_municipal || "",
    nacional_codigo_municipio: config.nacional_codigo_municipio || "",
    indicador_operacao: config.indicador_operacao || "",
    cst_ibscbs: config.cst_ibscbs || "",
    cclass_trib_ibscbs: config.cclass_trib_ibscbs || "",
    p_tot_trib_sn: config.p_tot_trib_sn != null ? String(config.p_tot_trib_sn) : "",
  };
}
