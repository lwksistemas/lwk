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

export type BusinessHoursBlock = {
  daysOfWeek: number[];
  startTime: string;
  endTime: string;
};

/** Expediente no FullCalendar, respeitando intervalo (ex.: almoço) como faixa excluída. */
export function businessHoursFromHorarios(horarios: HorarioTrabalho[]): BusinessHoursBlock[] {
  const ativos = horarios.filter((h) => h.ativo);
  if (!ativos.length) {
    return [{ daysOfWeek: [1, 2, 3, 4, 5], startTime: "08:00", endTime: "18:00" }];
  }
  const blocks: BusinessHoursBlock[] = [];
  for (const h of ativos) {
    const fcDay = h.dia_semana === 6 ? 0 : h.dia_semana + 1;
    const entrada = (h.hora_entrada || "08:00").slice(0, 5);
    const saida = (h.hora_saida || "18:00").slice(0, 5);
    if (h.intervalo_inicio && h.intervalo_fim) {
      const intIni = h.intervalo_inicio.slice(0, 5);
      const intFim = h.intervalo_fim.slice(0, 5);
      blocks.push({ daysOfWeek: [fcDay], startTime: entrada, endTime: intIni });
      blocks.push({ daysOfWeek: [fcDay], startTime: intFim, endTime: saida });
    } else {
      blocks.push({ daysOfWeek: [fcDay], startTime: entrada, endTime: saida });
    }
  }
  return blocks;
}

/** Eventos visuais de intervalo (almoço) para o calendário da agenda. */
export function intervalosEventsFromHorarios(
  profId: string,
  horarios: HorarioTrabalho[],
  profName: string,
  dias = 90,
) {
  const result: Array<Record<string, unknown>> = [];
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  for (let i = 0; i < dias; i++) {
    const data = new Date(hoje);
    data.setDate(hoje.getDate() + i);
    const diaBackend = weekdayFromDate(data);
    const horario = horarios.find((h) => h.ativo && h.dia_semana === diaBackend);
    if (!horario?.intervalo_inicio || !horario?.intervalo_fim) continue;
    const y = data.getFullYear();
    const m = String(data.getMonth() + 1).padStart(2, "0");
    const d = String(data.getDate()).padStart(2, "0");
    const ini = horario.intervalo_inicio.slice(0, 5);
    const fim = horario.intervalo_fim.slice(0, 5);
    result.push({
      id: `intervalo-${profId}-${y}${m}${d}`,
      title: `🍽️ Intervalo ${ini}–${fim}`,
      start: `${y}-${m}-${d}T${ini}:00`,
      end: `${y}-${m}-${d}T${fim}:00`,
      allDay: false,
      backgroundColor: "#f59e0b",
      borderColor: "#d97706",
      textColor: "#fff",
      editable: false,
      extendedProps: { isIntervalo: true, professional_name: profName, intervalo_inicio: ini, intervalo_fim: fim },
    });
  }
  return result;
}
