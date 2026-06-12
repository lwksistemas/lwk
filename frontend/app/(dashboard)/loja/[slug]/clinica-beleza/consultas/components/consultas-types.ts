export interface LocalAtendimento {
  id: number;
  nome: string;
  valor_consulta: string | number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConsultaProcedimento {
  id: number;
  nome: string;
  valor: number;
}

export interface Consulta {
  id: number;
  patient: number;
  procedure: number;
  professional?: number | null;
  patient_name: string;
  professional_name: string;
  procedure_name: string;
  procedures_list?: ConsultaProcedimento[];
  protocol?: number | null;
  protocol_name?: string | null;
  status: string;
  data_inicio?: string | null;
  data_fim?: string | null;
  observacoes_gerais?: string;
  protocolo_notas?: string;
  valor_consulta: string | number;
  /** Soma dos procedimentos do agendamento. */
  valor_procedimentos?: string | number;
  /** Total a cobrar: taxa de consulta + procedimentos. */
  valor_pagamento?: string | number;
  local_atendimento?: number | null;
  local_atendimento_name?: string | null;
  convenio?: number | null;
  convenio_name?: string | null;
  nome_agenda_id?: number | null;
  nome_agenda_name?: string | null;
  appointment_date?: string;
  appointment_status?: string;
  total_evolucoes: number;
  status_assinatura_termo?: string;
  status_assinatura_termo_display?: string;
  exige_termo_consentimento?: boolean;
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

export type TabId = "atendimento" | "produtos" | "anamnese" | "evolucao" | "historico" | "documentos" | "fotos";

export interface ConsultaProdutoUtilizado {
  id: number;
  produto: number;
  produto_nome: string;
  quantidade: number | string;
  lote: string;
  validade: string | null;
  unidade_medida?: string;
  estoque_baixado?: boolean;
}

export function consultaProcedimentos(c: Consulta): ConsultaProcedimento[] {
  if (c.procedures_list?.length) return c.procedures_list;
  if (c.procedure_name) {
    return [{
      id: c.procedure,
      nome: c.procedure_name,
      valor: Number(c.valor_procedimentos ?? 0),
    }];
  }
  return [];
}

export function consultaProcedimentosNomes(c: Consulta): string {
  const nomes = consultaProcedimentos(c).map((p) => (p.nome || "").toUpperCase());
  return nomes.length ? nomes.join(" · ") : "—";
}

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
