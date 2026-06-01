export interface Consulta {
  id: number;
  patient: number;
  procedure: number;
  professional?: number | null;
  patient_name: string;
  professional_name: string;
  procedure_name: string;
  protocol?: number | null;
  protocol_name?: string | null;
  status: string;
  data_inicio?: string | null;
  data_fim?: string | null;
  observacoes_gerais?: string;
  protocolo_notas?: string;
  valor_consulta: string | number;
  appointment_date?: string;
  appointment_status?: string;
  total_evolucoes: number;
}

export interface Protocolo {
  id: number;
  nome: string;
  procedure: number;
  descricao?: string;
  preparacao?: string;
  execucao?: string;
  pos_procedimento?: string;
  materiais_necessarios?: string;
}

export interface Anamnese {
  queixa_principal: string;
  historico_medico: string;
  medicamentos_uso: string;
  alergias: string;
  condicoes_clinicas: string;
  tipo_pele: string;
  pressao_arterial: string;
  peso: string | number | null;
  altura: string | number | null;
  observacoes: string;
}

export interface Evolucao {
  id: number;
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  protocolo_snapshot: string;
  satisfacao?: number | null;
  created_at: string;
  professional_name?: string;
}

export type TabId = "atendimento" | "anamnese" | "evolucao" | "historico";

export const EMPTY_ANAMNESE: Anamnese = {
  queixa_principal: "",
  historico_medico: "",
  medicamentos_uso: "",
  alergias: "",
  condicoes_clinicas: "",
  tipo_pele: "",
  pressao_arterial: "",
  peso: "",
  altura: "",
  observacoes: "",
};

export const ANAMNESE_FIELDS = [
  ["queixa_principal", "Queixa principal"],
  ["historico_medico", "Histórico médico"],
  ["medicamentos_uso", "Medicamentos em uso"],
  ["alergias", "Alergias"],
  ["condicoes_clinicas", "Condições clínicas"],
  ["tipo_pele", "Tipo de pele"],
  ["pressao_arterial", "Pressão arterial"],
  ["observacoes", "Observações"],
] as const;
