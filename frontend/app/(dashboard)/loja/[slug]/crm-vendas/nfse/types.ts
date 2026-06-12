import type { MouseEvent } from 'react';

/** Item da listagem NFS-e (loja CRM). */
export interface NFSe {
  id: number;
  numero_nf: string;
  numero_rps: number;
  codigo_verificacao: string;
  data_emissao: string;
  valor: string;
  valor_iss: string;
  aliquota_iss: string;
  valor_liquido: number;
  tomador_nome: string;
  tomador_cpf_cnpj: string;
  tomador_email?: string;
  servico_descricao: string;
  status: string;
  status_display: string;
  provedor_display: string;
  provedor?: string;
  asaas_invoice_id?: string;
  erro?: string;
}

export type NfseLojaRowHandlers = {
  onSync: (e: MouseEvent, nf: NFSe) => void;
  onDelete: (e: MouseEvent, nf: NFSe) => void;
  onDownloadPdf: (e: MouseEvent, nf: NFSe) => void;
  onReenviarEmail: (e: MouseEvent, nf: NFSe) => void;
  onEnviarWhatsapp: (e: MouseEvent, nf: NFSe) => void;
  onCancelar: (nf: NFSe) => void;
  whatsappHabilitado?: boolean;
};
