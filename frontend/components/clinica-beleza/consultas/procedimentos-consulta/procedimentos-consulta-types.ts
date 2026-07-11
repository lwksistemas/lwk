import type { ConsultaProcedimento } from "../consultas-types";

export interface ProcedureOption {
  id: number;
  nome: string;
  categoria?: string;
}

export interface AppointmentProcedureItem {
  id: number;
  procedure: number;
  procedure_name: string;
  valor_efetivo: number;
}

export const PROCEDIMENTOS_SELECT_CLASS =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";
