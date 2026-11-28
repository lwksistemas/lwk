import type { RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";

export function formatDuracaoPrevista(minutos: number): string {
  if (!minutos || minutos <= 0) return "Não definida";
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h > 0 && m > 0) return `${h}h ${m}min`;
  if (h > 0) return `${h}h`;
  return `${m}min`;
}

export const RETORNO_AVALIACAO_ISENTA_TITULO = "Retorno com avaliação isenta";

function diasRestantesRetorno(info: RetornoVerificacaoResult): number | null {
  const dias = info.dias_restantes;
  if (dias == null || Number.isNaN(Number(dias))) return null;
  return Math.max(0, Number(dias));
}

/** Texto curto para o card de resumo — evita corte da mensagem longa da API. */
export function formatRetornoResumoCompact(info: RetornoVerificacaoResult | null | undefined): string {
  if (!info?.elegivel) return "Não informado";
  const n = diasRestantesRetorno(info);
  if (n == null) return "Avaliação isenta";
  return `Avaliação isenta · ${n} ${n === 1 ? "dia restante" : "dias restantes"}`;
}

/** Corpo do aviso verde no modal (somente texto; regras financeiras inalteradas). */
export function formatRetornoBannerMensagem(
  info: RetornoVerificacaoResult | null | undefined,
  temProcedimentos: boolean,
): string {
  if (!info?.elegivel) return "";
  const n = diasRestantesRetorno(info);
  const prazo =
    n == null
      ? "Prazo de retorno sem taxa de avaliação."
      : `${n} ${n === 1 ? "dia restante" : "dias restantes"} para retorno sem taxa de avaliação.`;
  if (!temProcedimentos) return prazo;
  return `${prazo} Os procedimentos selecionados serão cobrados conforme os valores apresentados.`;
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
