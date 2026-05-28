/** Item da listagem NFS-e emitidas (superadmin). */
export interface NFSeEmitida {
  id: number;
  numero_nf: string;
  codigo_verificacao: string;
  numero_rps: number;
  serie_rps: string;
  provedor: 'nacional' | 'issnet' | 'asaas';
  status: 'emitida' | 'cancelada' | 'erro' | 'pendente';
  valor: string;
  aliquota_iss: string;
  valor_iss: string;
  tomador_nome: string;
  tomador_cpf_cnpj: string;
  tomador_email: string;
  descricao_servico: string;
  loja_nome: string;
  loja_slug: string;
  asaas_payment_id: string;
  data_emissao: string | null;
  data_cancelamento: string | null;
  created_at: string | null;
  tem_xml: boolean;
  pdf_url: string;
  erro_mensagem: string;
}

export type NfseSuperadminHandlers = {
  onBaixarPdf: (nf: NFSeEmitida) => void;
  onBaixarXml: (nf: NFSeEmitida) => void;
  onReenviar: (nf: NFSeEmitida) => void;
  onCancelar: (nf: NFSeEmitida) => void;
  onExcluir: (nf: NFSeEmitida) => void;
};
