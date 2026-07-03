import {
  entityName,
  procedureCategoria,
  procedureDescription,
  procedureDuration,
} from "@/lib/clinica-beleza-entities";
import { resolveProcedureCategoriaSlug } from "@/lib/clinica-beleza-categories";

export interface Procedure {
  id: number;
  name?: string;
  nome?: string;
  description?: string | null;
  descricao?: string | null;
  price?: string;
  preco?: string;
  duration?: number;
  duracao_minutos?: number;
  active?: boolean;
  is_active?: boolean;
  categoria?: string;
  termo_consentimento?: string;
  termo_consentimento_ativo?: boolean;
}

export interface ProcedimentoFormState {
  name: string;
  description: string;
  duration: string;
  categoria: string;
  termo_consentimento: string;
  termo_consentimento_ativo: boolean;
}

export const DEFAULT_TERMO_CONSENTIMENTO = `TERMO DE CONSENTIMENTO ESCLARECIDO

Eu, {paciente_nome}, inscrito(a) no CPF {paciente_cpf}, declaro ter sido esclarecido(a) sobre o(s) procedimento(s): {procedimentos}, a serem realizados pela profissional {profissional_nome} ({profissional_conselho}) na clínica {clinica_nome}.

Fui informado(a) sobre objetivos, benefícios, riscos, efeitos adversos, contraindicações e alternativas, e tive oportunidade de esclarecer minhas dúvidas.

Declaro que concordo com a realização do(s) procedimento(s) na data {data}.`;

export const EMPTY_PROCEDIMENTO_FORM: ProcedimentoFormState = {
  name: "",
  description: "",
  duration: "30",
  categoria: "",
  termo_consentimento: DEFAULT_TERMO_CONSENTIMENTO,
  termo_consentimento_ativo: false,
};

export const FORM_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

export const FORM_LABEL_CLASS = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";

export const FORM_SECTION_TITLE_CLASS =
  "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2";

export interface ProcedimentosPageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}

export function procedureToForm(p: Procedure): ProcedimentoFormState {
  return {
    name: entityName(p),
    description: procedureDescription(p) || "",
    duration: String(procedureDuration(p)),
    categoria: resolveProcedureCategoriaSlug(procedureCategoria(p)),
    termo_consentimento: (p.termo_consentimento || "").trim() || DEFAULT_TERMO_CONSENTIMENTO,
    termo_consentimento_ativo: !!p.termo_consentimento_ativo,
  };
}
