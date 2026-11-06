/** Passos aceitos na grade da agenda. Vazio no cadastro continua 15. */
export const INTERVALOS_AGENDA_MIN = [5, 10, 15, 20, 30, 45, 60] as const;

export const INTERVALO_AGENDA_PADRAO = 15;

export function intervaloAgendaMinutos(
  prof?: { intervalo_agenda_minutos?: number | null } | null,
): number {
  const n = Number(prof?.intervalo_agenda_minutos);
  if ((INTERVALOS_AGENDA_MIN as readonly number[]).includes(n)) return n;
  return INTERVALO_AGENDA_PADRAO;
}

/** Duração do FullCalendar. 60 vira 01:00:00. */
export function duracaoSlotAgenda(minutos: number): string {
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`;
}
