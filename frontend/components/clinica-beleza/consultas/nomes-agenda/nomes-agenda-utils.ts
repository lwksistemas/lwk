import { formatApiErrorBody } from "@/lib/api-errors";

export function extractNomesAgendaError(err: unknown, fallback: string): string {
  return formatApiErrorBody(err) || fallback;
}
