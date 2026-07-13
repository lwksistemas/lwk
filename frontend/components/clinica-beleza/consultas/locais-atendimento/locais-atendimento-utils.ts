import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatApiErrorBody } from "@/lib/api-errors";

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
  return formatApiErrorBody(err) || fallback;
}
