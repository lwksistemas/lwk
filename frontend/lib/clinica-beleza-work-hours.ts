/** Horário de trabalho do profissional (API clinica-beleza). */
export interface HorarioTrabalho {
  id?: number;
  dia_semana: number;
  hora_entrada: string;
  hora_saida: string;
  intervalo_inicio: string | null;
  intervalo_fim: string | null;
  ativo: boolean;
}

/** JS Date → dia_semana do backend (0=segunda … 6=domingo). */
export function weekdayFromDate(date: Date): number {
  const js = date.getDay();
  return js === 0 ? 6 : js - 1;
}

function parseHm(value: string): number {
  const [h, m] = value.slice(0, 5).split(':').map(Number);
  return h * 60 + (m || 0);
}

/**
 * Verifica se o intervalo [date, date+durationMin] cabe no expediente.
 * Se não houver horários cadastrados, permite (compatibilidade).
 */
export function isWithinWorkHours(
  date: Date,
  durationMin: number,
  horarios: HorarioTrabalho[],
): boolean {
  const ativos = horarios.filter((h) => h.ativo);
  if (!ativos.length) return true;

  const day = weekdayFromDate(date);
  const h = ativos.find((x) => x.dia_semana === day);
  if (!h) return false;

  const startMin = date.getHours() * 60 + date.getMinutes();
  const endMin = startMin + durationMin;
  const entryMin = parseHm(h.hora_entrada);
  const exitMin = parseHm(h.hora_saida);

  if (startMin < entryMin || endMin > exitMin) return false;

  if (h.intervalo_inicio && h.intervalo_fim) {
    const intStart = parseHm(h.intervalo_inicio);
    const intEnd = parseHm(h.intervalo_fim);
    if (startMin < intEnd && endMin > intStart) return false;
  }

  return true;
}

export function workHoursRejectionMessage(
  date: Date,
  durationMin: number,
  horarios: HorarioTrabalho[],
): string | null {
  const ativos = horarios.filter((h) => h.ativo);
  if (!ativos.length) return null;

  const day = weekdayFromDate(date);
  const h = ativos.find((x) => x.dia_semana === day);
  if (!h) {
    return 'Profissional não trabalha neste dia da semana.';
  }

  if (isWithinWorkHours(date, durationMin, horarios)) return null;

  const entrada = h.hora_entrada.slice(0, 5);
  const saida = h.hora_saida.slice(0, 5);
  if (h.intervalo_inicio && h.intervalo_fim) {
    const ini = h.intervalo_inicio.slice(0, 5);
    const fim = h.intervalo_fim.slice(0, 5);
    return `Horário fora do expediente (${entrada}–${saida}, intervalo ${ini}–${fim}).`;
  }
  return `Horário fora do expediente do profissional (${entrada}–${saida}).`;
}
