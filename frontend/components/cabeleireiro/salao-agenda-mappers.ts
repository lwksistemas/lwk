import type { SalaoAgendamento, SalaoServico } from '@/lib/cabeleireiro-api';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

export type SalaoCalendarEvent = {
  id: string;
  title: string;
  start: string;
  end: string;
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  extendedProps: {
    agendamento: SalaoAgendamento;
  };
};

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  SCHEDULED: { bg: '#C4A4B0', border: '#4A3042', text: '#1f1220' },
  CLIENT_CONFIRMED: { bg: '#86efac', border: '#16a34a', text: '#14532d' },
  ARRIVED: { bg: '#93c5fd', border: '#2563eb', text: '#1e3a8a' },
  IN_PROGRESS: { bg: '#fcd34d', border: '#d97706', text: '#78350f' },
  DONE: { bg: '#d1d5db', border: '#6b7280', text: '#374151' },
  NO_SHOW: { bg: '#fca5a5', border: '#dc2626', text: '#7f1d1d' },
  CANCELLED: { bg: '#e5e7eb', border: '#9ca3af', text: '#6b7280' },
};

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
  const colors = STATUS_COLORS[ag.status] || {
    bg: SALAO_PRIMARY,
    border: SALAO_PRIMARY,
    text: '#ffffff',
  };
  const title = [
    ag.cliente_nome,
    ag.servico_nome,
  ]
    .filter(Boolean)
    .join(' · ');

  return {
    id: String(ag.id),
    title: title || 'Agendamento',
    start,
    end,
    backgroundColor: colors.bg,
    borderColor: colors.border,
    textColor: colors.text,
    extendedProps: { agendamento: ag },
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

export function dateFromFc(date: Date) {
  return {
    data: toLocalIsoDate(date),
    hora_inicio: `${pad2(date.getHours())}:${pad2(date.getMinutes())}`,
  };
}
