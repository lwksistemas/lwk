const WEEKDAYS = [
  'domingo',
  'segunda-feira',
  'terça-feira',
  'quarta-feira',
  'quinta-feira',
  'sexta-feira',
  'sábado',
];

const MONTHS = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
];

export const SIDEBAR_HIDDEN_KEY = 'clinica-geral-sidebar-hidden';

export function toISODate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function parseISODate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, (m || 1) - 1, d || 1);
}

export function addDays(iso: string, days: number): string {
  const d = parseISODate(iso);
  d.setDate(d.getDate() + days);
  return toISODate(d);
}

export function formatLongDate(iso: string): string {
  const d = parseISODate(iso);
  return `${WEEKDAYS[d.getDay()]} ${d.getDate()} de ${MONTHS[d.getMonth()]} de ${d.getFullYear()}`;
}

export function formatShortDate(iso: string): string {
  const d = parseISODate(iso);
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  return `${WEEKDAYS[d.getDay()]}, ${dd}/${mm}/${d.getFullYear()}`;
}

export function formatHora(hora: string): string {
  return (hora || '').slice(0, 5);
}

export function displayName(nome: string, nomeSocial?: string | null): string {
  const social = (nomeSocial || '').trim();
  if (social) return `${social} (${nome})`;
  return nome;
}

export function ageFromISO(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const birth = parseISODate(iso);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age -= 1;
  return age >= 0 ? age : null;
}

export function slotTimes(startHour = 8, endHour = 18, stepMin = 15): string[] {
  const out: string[] = [];
  for (let h = startHour; h < endHour; h += 1) {
    for (let min = 0; min < 60; min += stepMin) {
      out.push(`${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`);
    }
  }
  return out;
}

export function monthGrid(year: number, month: number): (number | null)[] {
  const first = new Date(year, month, 1);
  const days = new Date(year, month + 1, 0).getDate();
  const cells: (number | null)[] = Array(first.getDay()).fill(null);
  for (let d = 1; d <= days; d += 1) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}

export function readSidebarHidden(): boolean {
  if (typeof window === 'undefined') return false;
  return window.localStorage.getItem(SIDEBAR_HIDDEN_KEY) === '1';
}

export function writeSidebarHidden(hidden: boolean): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(SIDEBAR_HIDDEN_KEY, hidden ? '1' : '0');
}

export function formatLivreHeading(iso: string, hoje: string): string {
  const d = parseISODate(iso);
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const weekday = WEEKDAYS[d.getDay()];
  const corpo = `${weekday} ${dd}/${mm}/${d.getFullYear()}`;
  if (iso === addDays(hoje, 1)) return `Amanhã, ${corpo}`;
  if (iso === hoje) return `Hoje, ${corpo}`;
  return corpo;
}

export function cardTone(status: string): { bg: string; border: string } {
  if (status === 'confirmado') return { bg: '#C8E6C0', border: '#7CB342' };
  if (status === 'recepcionado') return { bg: '#B2DFDB', border: '#00897B' };
  if (status === 'atendido') return { bg: '#E0E0E0', border: '#9E9E9E' };
  if (status === 'faltou') return { bg: '#FFCDD2', border: '#E57373' };
  return { bg: '#C5E1A5', border: '#8BC34A' };
}

export function monthRange(ref = new Date()): { de: string; ate: string } {
  const de = toISODate(new Date(ref.getFullYear(), ref.getMonth(), 1));
  const ate = toISODate(new Date(ref.getFullYear(), ref.getMonth() + 1, 0));
  return { de, ate };
}

export function whatsappHref(phone: string): string | null {
  const d = (phone || '').replace(/\D/g, '');
  if (d.length < 10) return null;
  const withCountry = d.startsWith('55') ? d : `55${d}`;
  return `https://wa.me/${withCountry}`;
}
