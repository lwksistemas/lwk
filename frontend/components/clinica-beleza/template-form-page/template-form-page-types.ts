export const TEMPLATE_TIPO_OPTIONS = [
  { value: "receituario", label: "Receituário" },
  { value: "pedido_exame", label: "Pedido de Exame" },
  { value: "atestado", label: "Atestado" },
  { value: "documento_personalizado", label: "Documento Personalizado" },
] as const;

export const TEMPLATE_PLACEHOLDERS = [
  { tag: "{{paciente_nome}}", desc: "Nome do paciente" },
  { tag: "{{paciente_cpf}}", desc: "CPF do paciente" },
  { tag: "{{paciente_data_nascimento}}", desc: "Data de nascimento" },
  { tag: "{{profissional_nome}}", desc: "Nome do profissional" },
  { tag: "{{profissional_registro}}", desc: "Nº registro profissional" },
  { tag: "{{profissional_conselho}}", desc: "Conselho com UF e nº (ex.: COREN-SP 123456)" },
  { tag: "{{data_atual}}", desc: "Data do dia (DD/MM/AAAA)" },
  { tag: "{{consulta_procedimento}}", desc: "Procedimento da consulta" },
] as const;

export interface TemplateFormState {
  nome: string;
  tipo: string;
  conteudo: string;
}

export const TEMPLATE_FORM_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";

export const TEMPLATE_FORM_LABEL_CLASS = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";

export const TEMPLATE_FORM_SECTION_TITLE_CLASS =
  "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2";
