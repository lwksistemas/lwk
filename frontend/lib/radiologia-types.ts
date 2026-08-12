/** Tipos do módulo Radiologia (RIS). */

export type PedidoStatus =
  | 'agendado'
  | 'na_worklist'
  | 'em_aquisicao'
  | 'imagens_recebidas'
  | 'em_laudo'
  | 'laudado'
  | 'entregue'
  | 'cancelado'
  | 'orfao';

export type LaudoStatus = 'rascunho' | 'finalizado' | 'assinado' | 'entregue';

export interface PacienteRadiologia {
  id: number;
  nome: string;
  cpf: string;
  data_nascimento: string | null;
  sexo: string;
  telefone: string;
  email: string;
  is_active: boolean;
}

export interface Equipamento {
  id: number;
  nome: string;
  ae_title: string;
  modality: string;
  fabricante: string;
  modelo: string;
  numero_serie: string;
  codigo_vinculo: string;
  station_name: string;
  suporte_dicom_storage: boolean;
  suporte_mwl: boolean;
  suporte_sr: boolean;
  cobranca_mensal: string | null;
  is_active: boolean;
}

export interface Procedimento {
  id: number;
  codigo: string;
  nome: string;
  modality: string;
  descricao: string;
  template_laudo: string;
  is_active: boolean;
}

export interface PedidoExame {
  id: number;
  paciente: number;
  paciente_nome: string;
  procedimento: number;
  procedimento_nome: string;
  equipamento: number | null;
  equipamento_nome: string | null;
  equipamento_ae_title?: string | null;
  medico_solicitante: string;
  crm_solicitante: string;
  indicacao_clinica: string;
  agendado_para: string;
  status: PedidoStatus;
  accession_number: string;
  study_instance_uid: string;
  orthanc_study_id: string;
  dicom_media_url: string;
  dicom_instance_count: number;
  dicom_synced_at: string | null;
  mwl_synced_at: string | null;
  observacoes: string;
}

export interface Laudo {
  id: number;
  pedido: number;
  accession_number: string;
  paciente_nome: string;
  medico_laudador: string;
  crm_laudador: string;
  texto: string;
  conclusao: string;
  bi_rads: string;
  status: LaudoStatus;
  pdf_url: string;
  assinado_em: string | null;
}

export const PEDIDO_STATUS_LABEL: Record<PedidoStatus, string> = {
  agendado: 'Agendado',
  na_worklist: 'Na worklist',
  em_aquisicao: 'Em aquisição',
  imagens_recebidas: 'Imagens recebidas',
  em_laudo: 'Em laudo',
  laudado: 'Laudado',
  entregue: 'Entregue',
  cancelado: 'Cancelado',
  orfao: 'Órfão',
};
