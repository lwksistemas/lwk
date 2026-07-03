export const RETORNO_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-800";

export function extractRetornoAgendaError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const val of Object.values(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return val[0];
    if (typeof val === "string") return val;
  }
  return fallback;
}
