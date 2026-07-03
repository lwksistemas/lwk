export interface TimbradoDetalhe {
  ok?: boolean;
  professional_id?: number;
  error?: string;
  detail?: string;
  status?: number;
}

export interface TimbradoStatus {
  tem_timbrado: boolean;
  pdf_nome?: string;
  tamanho_bytes?: number;
  updated_at?: string | null;
  aplicados?: number;
  total?: number;
  warning?: string;
  detalhes?: TimbradoDetalhe[];
}

export interface MemedDiagStatus {
  environment?: string;
  credentials_configured?: boolean;
  production_keys_configured?: boolean;
  profissionais_com_cpf?: number;
  ready_for_production?: boolean;
}
