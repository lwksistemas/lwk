import { formatApiErrorBody } from "@/lib/api-errors";

export const RETORNO_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-800";

export function extractRetornoAgendaError(err: unknown, fallback: string): string {
  return formatApiErrorBody(err) || fallback;
}
