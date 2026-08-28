export interface TimbradoDetalhe {
  ok?: boolean;
  professional_id?: number;
  nome?: string;
  error?: string;
  detail?: string;
  status?: number;
  status_memed?: string;
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

export interface MemedPrescritorDiag {
  professional_id?: number;
  nome?: string;
  state?: string;
  status?: string;
  label?: string;
  terms_accepted?: boolean;
  tem_token?: boolean;
  pode_prescrever?: boolean;
}

export interface MemedDiagStatus {
  environment?: string;
  credentials_configured?: boolean;
  production_keys_configured?: boolean;
  profissionais_com_cpf?: number;
  prescritores?: MemedPrescritorDiag[];
  prescritores_liberados?: number;
  ready_for_production?: boolean;
}
