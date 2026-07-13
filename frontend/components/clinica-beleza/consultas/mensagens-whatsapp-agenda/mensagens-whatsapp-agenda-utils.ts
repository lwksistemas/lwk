import { formatApiErrorBody } from "@/lib/api-errors";

export function extractMensagemWhatsAppError(err: unknown, fallback: string): string {
  return formatApiErrorBody(err) || fallback;
}
