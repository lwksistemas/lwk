import { formatCurrency } from "@/lib/financeiro-helpers";

export function parseValorInput(value: string): number {
  const trimmed = value.trim();
  if (!trimmed) return NaN;
  if (trimmed.includes(",")) {
    return parseFloat(trimmed.replace(/\./g, "").replace(",", "."));
  }
  return parseFloat(trimmed);
}

export function valorToInput(value: string | number | null | undefined): string {
  if (value == null || value === "") return "";
  const num = typeof value === "string" ? parseFloat(value.replace(",", ".")) : Number(value);
  return Number.isFinite(num) ? String(num) : "";
}

export function formatCurrencyBR(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value.replace(",", ".")) : value;
  if (!Number.isFinite(num)) return "—";
  return formatCurrency(num);
}

export function extractLocaisAtendimentoError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const [key, val] of Object.entries(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return `${key}: ${val[0]}`;
    if (typeof val === "string") return val;
  }
  return fallback;
}
