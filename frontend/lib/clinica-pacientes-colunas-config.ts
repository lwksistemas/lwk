/** Definições de colunas configuráveis na listagem de Clientes (clínica). */

import {
  colunasVisiveisFromConfig,
  type CrmColunaDef,
} from "@/lib/crm-colunas-config";

export type PacientesColunaDef = CrmColunaDef;

export const COLUNAS_PACIENTES_DISPONIVEIS: PacientesColunaDef[] = [
  { key: "nome", label: "Nome" },
  { key: "telefone", label: "Telefone" },
  { key: "email", label: "E-mail" },
  { key: "cpf", label: "CPF" },
  { key: "convenio", label: "Convênio" },
  { key: "data_nascimento", label: "Nascimento" },
  { key: "cidade", label: "Cidade" },
  { key: "sexo", label: "Sexo" },
];

/** Padrão da listagem atual, sem a coluna Ações. */
export const DEFAULT_COLUNAS_PACIENTES = [
  "nome",
  "telefone",
  "email",
  "cpf",
  "convenio",
];

export function resolveColunasPacientes(
  keys: string[] | undefined | null,
): PacientesColunaDef[] {
  return colunasVisiveisFromConfig(
    keys,
    COLUNAS_PACIENTES_DISPONIVEIS,
    DEFAULT_COLUNAS_PACIENTES,
  );
}
