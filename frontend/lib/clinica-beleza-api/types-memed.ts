/** Tipos Memed / fotos usados pelo client de consultas. */
export interface PacienteFotoItem {
  id: number;
  cloudinary_url: string;
  origem: string;
  origem_display: string;
  consulta_id: number;
  consulta_data: string;
  created_at: string;
}

export interface PrescricaoMemedItemDetalhe {
  nome?: string;
  posologia?: string;
  tipo?: string;
  receituario?: string;
}

/** Prescrição Memed registrada no histórico do paciente. */
export interface PrescricaoMemedItem {
  id: number;
  consulta: number | null;
  patient: number;
  patient_name?: string;
  professional: number | null;
  professional_name?: string | null;
  prescricao_id: string;
  resumo: string;
  itens: PrescricaoMemedItemDetalhe[];
  pdf_url?: string;
  created_at: string;
}
