export interface Protocol {
  id: number;
  nome: string;
  procedure: number;
  procedure_name?: string;
  procedure_categoria?: string;
  descricao?: string;
  tempo_estimado: number;
  materiais_necessarios?: string;
  preparacao?: string;
  execucao?: string;
  pos_procedimento?: string;
  contraindicacoes?: string;
  cuidados_especiais?: string;
  created_at?: string;
}

export interface ProtocoloProcedureOption {
  id: number;
  nome?: string;
  name?: string;
  categoria?: string;
}

export interface ProtocoloFormState {
  nome: string;
  procedure: string;
  descricao: string;
  tempo_estimado: string;
  materiais_necessarios: string;
  preparacao: string;
  execucao: string;
  pos_procedimento: string;
  contraindicacoes: string;
  cuidados_especiais: string;
}

export const EMPTY_PROTOCOLO_FORM: ProtocoloFormState = {
  nome: "",
  procedure: "",
  descricao: "",
  tempo_estimado: "30",
  materiais_necessarios: "",
  preparacao: "",
  execucao: "",
  pos_procedimento: "",
  contraindicacoes: "",
  cuidados_especiais: "",
};

export const FORM_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

export const FORM_LABEL_CLASS = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";

export const FORM_SECTION_TITLE_CLASS =
  "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2";

export const PROTOCOLO_FORM_FIELDS_LEFT = [["descricao", "Descrição"]] as const;

export const PROTOCOLO_FORM_FIELDS_RIGHT = [
  ["materiais_necessarios", "Materiais necessários"],
  ["preparacao", "Preparação"],
  ["execucao", "Execução (passos)"],
  ["pos_procedimento", "Pós-procedimento"],
  ["contraindicacoes", "Contraindicações"],
  ["cuidados_especiais", "Cuidados especiais"],
] as const;

export type ProtocoloFormTextFieldKey =
  | (typeof PROTOCOLO_FORM_FIELDS_LEFT)[number][0]
  | (typeof PROTOCOLO_FORM_FIELDS_RIGHT)[number][0];

export interface ProtocolosPageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}
