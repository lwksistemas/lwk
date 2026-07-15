import type { SalaoAgendamento, SalaoBloqueio, SalaoServico } from '@/lib/cabeleireiro-api';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

export type SalaoCalendarEvent = {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  editable?: boolean;
  extendedProps: {
    agendamento?: SalaoAgendamento;
    isBloqueio?: boolean;
    bloqueioId?: number;
    motivo?: string;
    professional_name?: string;
    status?: string;
    patient_name?: string;
    procedure_name?: string;
  };
};

/** Cores alinhadas à clínica — CLIENT_CONFIRMED = ciano (WhatsApp). */
export const SALAO_STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  SCHEDULED: { bg: '#a855f7', border: '#9333ea', text: '#ffffff' },
  CLIENT_CONFIRMED: { bg: '#06b6d4', border: '#0891b2', text: '#ffffff' },
  ARRIVED: { bg: '#22c55e', border: '#16a34a', text: '#ffffff' },
  IN_PROGRESS: { bg: '#8b5cf6', border: '#7c3aed', text: '#ffffff' },
  DONE: { bg: '#047857', border: '#065f46', text: '#ffffff' },
  NO_SHOW: { bg: '#b45309', border: '#92400e', text: '#ffffff' },
  CANCELLED: { bg: '#dc2626', border: '#b91c1c', text: '#ffffff' },
};

export const SALAO_STATUS_LABEL: Record<string, string> = {
  SCHEDULED: 'Agendado',
  CLIENT_CONFIRMED: 'Confirmado (WhatsApp)',
  ARRIVED: 'Chegou',
  IN_PROGRESS: 'Em atendimento',
  DONE: 'Concluído',
  NO_SHOW: 'Não compareceu',
  CANCELLED: 'Cancelado',
};

export const SALAO_AGENDA_STATUS_COLOR_EDITABLE = [
  'SCHEDULED',
  'CLIENT_CONFIRMED',
  'ARRIVED',
  'IN_PROGRESS',
  'DONE',
  'NO_SHOW',
  'CANCELLED',
] as const;

export type SalaoStatusColorMap = Record<string, { bg: string; border: string; text?: string }>;

export function mergeSalaoAgendaStatusColors(
  overrides?: Record<string, { bg?: string; border?: string }> | null,
): SalaoStatusColorMap {
  const merged: SalaoStatusColorMap = { ...SALAO_STATUS_COLORS };
  if (!overrides || typeof overrides !== 'object') return merged;
  for (const key of SALAO_AGENDA_STATUS_COLOR_EDITABLE) {
    const entry = overrides[key];
    if (!entry) continue;
    const bg = typeof entry.bg === 'string' ? entry.bg.trim() : '';
    const border = typeof entry.border === 'string' ? entry.border.trim() : '';
    if (/^#[0-9A-Fa-f]{6}$/.test(bg) && /^#[0-9A-Fa-f]{6}$/.test(border)) {
      merged[key] = { bg: bg.toLowerCase(), border: border.toLowerCase(), text: '#ffffff' };
    }
  }
  return merged;
}

export const SALAO_BLOQUEIO_COLORS = { bg: '#4f46e5', border: '#4338ca', text: '#ffffff' };

function pad2(n: number) {
  return String(n).padStart(2, '0');
}

function toLocalIsoDate(d: Date) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function parseHora(h: string) {
  const parts = (h || '09:00').slice(0, 5).split(':').map(Number);
  return { hours: parts[0] || 0, minutes: parts[1] || 0 };
}

function addMinutes(data: string, hora: string, minutes: number) {
  const { hours, minutes: mins } = parseHora(hora);
  const [y, m, d] = data.split('-').map(Number);
  const dt = new Date(y, (m || 1) - 1, d || 1, hours, mins, 0, 0);
  dt.setMinutes(dt.getMinutes() + minutes);
  return `${toLocalIsoDate(dt)}T${pad2(dt.getHours())}:${pad2(dt.getMinutes())}:00`;
}

export function salaoAgendamentoToEvent(
  ag: SalaoAgendamento,
  servicosById?: Map<number, SalaoServico>,
  statusColors?: SalaoStatusColorMap,
): SalaoCalendarEvent {
  const startHora = (ag.hora_inicio || '09:00').slice(0, 5);
  const start = `${ag.data}T${startHora}:00`;
  let end: string;
  if (ag.hora_fim) {
    end = `${ag.data}T${(ag.hora_fim || '').slice(0, 5)}:00`;
  } else {
    const dur =
      (ag.servico && servicosById?.get(ag.servico)?.duracao_minutos) ||
      40;
    end = addMinutes(ag.data, startHora, dur);
  }
  const palette = statusColors || SALAO_STATUS_COLORS;
  const colors = palette[ag.status] || {
    bg: SALAO_PRIMARY,
    border: SALAO_PRIMARY,
    text: '#ffffff',
  };
  const title = [ag.cliente_nome, ag.servico_nome].filter(Boolean).join(' · ');

  return {
    id: String(ag.id),
    title: title || 'Agendamento',
    start,
    end,
    backgroundColor: colors.bg,
    borderColor: colors.border,
    textColor: colors.text || '#ffffff',
    extendedProps: {
      agendamento: ag,
      status: ag.status,
      patient_name: ag.cliente_nome,
      procedure_name: ag.servico_nome,
      professional_name: ag.profissional_nome,
    },
  };
}

export function salaoBloqueioToEvent(b: SalaoBloqueio): SalaoCalendarEvent {
  const rawS = b.data_inicio ?? '';
  const rawE = b.data_fim ?? '';
  const hasT = typeof rawS === 'string' && rawS.includes('T') && typeof rawE === 'string' && rawE.includes('T');
  const start = hasT ? rawS : `${String(rawS).slice(0, 10)}T00:00:00`;
  const end = hasT ? rawE : `${String(rawE || rawS).slice(0, 10)}T23:59:59`;
  return {
    id: `bloqueio-${b.id}`,
    title: `🚫 ${b.motivo}`,
    start,
    end,
    backgroundColor: SALAO_BLOQUEIO_COLORS.bg,
    borderColor: SALAO_BLOQUEIO_COLORS.border,
    textColor: SALAO_BLOQUEIO_COLORS.text,
    editable: true,
    extendedProps: {
      isBloqueio: true,
      bloqueioId: b.id,
      motivo: b.motivo,
      professional_name: b.professional_name || 'Todos',
      status: 'BLOQUEIO',
    },
  };
}

export function formatDateRangeISO(start: Date, end: Date) {
  // FullCalendar end is exclusive
  const endInclusive = new Date(end.getTime() - 1);
  return {
    data_inicio: toLocalIsoDate(start),
    data_fim: toLocalIsoDate(endInclusive),
  };
}

export function weekRangeAround(date = new Date()) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  const day = d.getDay();
  const diffToMon = day === 0 ? -6 : 1 - day;
  const start = new Date(d);
  start.setDate(d.getDate() + diffToMon);
  const endExclusive = new Date(start);
  endExclusive.setDate(start.getDate() + 7);
  return formatDateRangeISO(start, endExclusive);
}

export function dateFromFc(date: Date) {
  return {
    data: toLocalIsoDate(date),
    hora_inicio: `${pad2(date.getHours())}:${pad2(date.getMinutes())}`,
  };
}

export function shiftRange(
  range: { data_inicio: string; data_fim: string },
  days: number,
): { data_inicio: string; data_fim: string } {
  const [y1, m1, d1] = range.data_inicio.split('-').map(Number);
  const [y2, m2, d2] = range.data_fim.split('-').map(Number);
  const a = new Date(y1, m1 - 1, d1);
  const b = new Date(y2, m2 - 1, d2);
  a.setDate(a.getDate() + days);
  b.setDate(b.getDate() + days);
  return { data_inicio: toLocalIsoDate(a), data_fim: toLocalIsoDate(b) };
}
