import type { LocalAtendimentoItem, NomeAgendaItem } from "@/lib/clinica-beleza-api";

export type ModalCriarAgendamentoMode = "agenda" | "consulta";

export interface CriarAgendamentoProfessional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
  especialidade?: string;
  tempo_consulta_minutos?: number | null;
}

export function formatTimeFromDate(date: Date): string {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

/** Opções de horário em intervalos de 15 min (mais estável que input type=time no Android). */
export function buildTimeSlotOptions(
  startHour = 6,
  endHour = 22,
  stepMinutes = 15,
): string[] {
  const opts: string[] = [];
  for (let h = startHour; h <= endHour; h++) {
    for (let m = 0; m < 60; m += stepMinutes) {
      if (h === endHour && m > 0) break;
      opts.push(`${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`);
    }
  }
  return opts;
}

export const CRIAR_AGENDAMENTO_TIME_SLOTS = buildTimeSlotOptions();

export function resolveDefaultNomeAgendaId(items: NomeAgendaItem[]): number | "" {
  if (items.length === 0) return "";
  const padrao = items.find((n) => n.is_padrao);
  return padrao?.id ?? items[0].id;
}

export function resolveDefaultLocalId(items: LocalAtendimentoItem[]): number | "" {
  if (items.length === 0) return "";
  const padrao = items.find((l) => l.is_padrao);
  return padrao?.id ?? items[0].id;
}

export function formatDateInputValue(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export const CRIAR_AGENDAMENTO_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";
