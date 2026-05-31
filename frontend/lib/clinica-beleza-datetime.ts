import {
  CLINICA_AGENDA_DURACAO_MIN_MIN,
  CLINICA_AGENDA_DURACAO_SNAP_MIN,
} from '@/lib/clinica-beleza-constants';

export function parseEventDate(value: string | Date | null | undefined): Date | null {
  if (!value) return null;
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatClinicaHora(date: Date): string {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

export function formatClinicaDia(date: Date): string {
  return date.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'short' });
}

export function formatClinicaDateTime(date: Date): string {
  return date.toLocaleString('pt-BR');
}

export function formatClinicaDataCurta(date: Date): string {
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

/** Para inputs datetime-local. */
export function formatDateTimeLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const h = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${y}-${m}-${day}T${h}:${min}`;
}

export function arredondarDuracaoAgendaMin(minutos: number): number {
  const snap = Math.round(minutos / CLINICA_AGENDA_DURACAO_SNAP_MIN) * CLINICA_AGENDA_DURACAO_SNAP_MIN;
  return Math.max(CLINICA_AGENDA_DURACAO_MIN_MIN, snap);
}
