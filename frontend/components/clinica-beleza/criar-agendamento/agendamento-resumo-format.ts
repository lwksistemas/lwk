import type { RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";

export function formatDuracaoPrevista(minutos: number): string {
  if (!minutos || minutos <= 0) return "Não definida";
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h > 0 && m > 0) return `${h}h ${m}min`;
  if (h > 0) return `${h}h`;
  return `${m}min`;
}

/** Texto curto para o card de resumo — evita corte da mensagem longa da API. */
export function formatRetornoResumoCompact(info: RetornoVerificacaoResult | null | undefined): string {
  if (!info?.elegivel) return "Não informado";
  const dias = info.dias_restantes;
  if (dias == null || Number.isNaN(Number(dias))) return "Retorno gratuito";
  const n = Math.max(0, Number(dias));
  return `Retorno gratuito · ${n} ${n === 1 ? "dia restante" : "dias restantes"}`;
}

/** HH:MM de término a partir do horário de início e da duração em minutos. */
export function formatTerminoPrevisto(time: string, duracaoMinutos: number): string | null {
  if (!time || !duracaoMinutos || duracaoMinutos <= 0) return null;
  const parts = time.split(":");
  const h = Number(parts[0]);
  const m = Number(parts[1] ?? 0);
  if (!Number.isFinite(h) || !Number.isFinite(m)) return null;
  const total = h * 60 + m + duracaoMinutos;
  const eh = Math.floor(total / 60) % 24;
  const em = total % 60;
  return `${String(eh).padStart(2, "0")}:${String(em).padStart(2, "0")}`;
}
