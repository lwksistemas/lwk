export type PerfilAcesso =
  | "administrador"
  | "profissional"
  | "recepcao"
  | "recepcionista"
  | "caixa"
  | "limpeza"
  | "estoque";

export interface ProfissionalProcedure {
  id: number;
  nome: string;
  preco?: number;
}

export interface ProfissionalCommission {
  id?: number;
  tipo: string;
  modo: string;
  valor: string;
  procedure?: number | null;
  procedure_name?: string;
  convenio?: number | null;
  convenio_nome?: string;
  convenio_codigo?: string;
  local_atendimento?: number | null;
  local_atendimento_nome?: string;
}

export interface ProfissionalFormState {
  name: string;
  specialty: string;
  phone: string;
  email: string;
  conselho: string;
  registro: string;
  uf: string;
  cpf: string;
  data_nascimento: string;
  sexo: string;
  criar_acesso: boolean;
  perfil: PerfilAcesso;
  username: string;
}

export const UFS_BR = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
  "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
];

export const CONSELHOS: [string, string][] = [
  ["CRM", "CRM - Medicina"],
  ["CRO", "CRO - Odontologia"],
  ["COREN", "COREN - Enfermagem"],
  ["CRF", "CRF - Farmácia"],
  ["CRP", "CRP - Psicologia"],
  ["CRN", "CRN - Nutrição"],
  ["CREFITO", "CREFITO - Fisioterapia/TO"],
  ["CRBM", "CRBM - Biomedicina"],
  ["CRMV", "CRMV - Veterinária"],
  ["CRFa", "CRFa - Fonoaudiologia"],
];

export const INPUT_CLASS =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";

export const LABEL_CLASS = "block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1";

export const DEFAULT_PROFISSIONAL_FORM: ProfissionalFormState = {
  name: "",
  specialty: "",
  phone: "",
  email: "",
  conselho: "",
  registro: "",
  uf: "",
  cpf: "",
  data_nascimento: "",
  sexo: "",
  criar_acesso: false,
  perfil: "profissional",
  username: "",
};

export type ProfissionalEditing = { id: number };
