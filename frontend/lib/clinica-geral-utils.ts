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

export function ageFromISO(iso: string | null | undefined, today = new Date()): number | null {
  if (!iso) return null;
  const birth = parseISODate(iso);
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age -= 1;
  return age >= 0 ? age : null;
}

export function formatDateBR(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = parseISODate(iso);
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  return `${dd}/${mm}/${d.getFullYear()}`;
}

export function formatAgeYearsMonths(iso: string | null | undefined, today = new Date()): string | null {
  if (!iso) return null;
  const birth = parseISODate(iso);
  if (birth > today) return null;
  let years = today.getFullYear() - birth.getFullYear();
  let months = today.getMonth() - birth.getMonth();
  if (today.getDate() < birth.getDate()) months -= 1;
  if (months < 0) {
    years -= 1;
    months += 12;
  }
  if (years < 0) return null;
  const yLabel = years === 1 ? '1 ano' : `${years} anos`;
  const mLabel = months === 1 ? '1 mês' : `${months} meses`;
  if (years === 0) return mLabel;
  if (months === 0) return yLabel;
  return `${yLabel} e ${mLabel}`;
}

export function formatProntuarioSubtitulo(p: {
  data_nascimento?: string | null;
  estado_civil?: string;
  cidade?: string;
  uf?: string;
}, today = new Date()): string {
  const partes: string[] = [];
  const idade = formatAgeYearsMonths(p.data_nascimento, today);
  if (idade) partes.push(idade);
  if (p.estado_civil?.trim()) partes.push(p.estado_civil.trim());
  const local = [p.cidade, p.uf].filter((s) => (s || '').trim()).join(' - ');
  if (local) partes.push(local);
  return partes.join('. ');
}

export function formatNascimentoIdade(iso: string | null | undefined, today = new Date()): string {
  if (!iso) return '';
  const idade = formatAgeYearsMonths(iso, today);
  return idade ? `${formatDateBR(iso)} (${idade})` : formatDateBR(iso);
}

export function daysFromToday(iso: string, today = new Date()): number {
  const ref = parseISODate(toISODate(today));
  const d = parseISODate(iso);
  return Math.round((d.getTime() - ref.getTime()) / 86400000);
}

export function formatDaysOffset(days: number): string {
  if (days === 0) return '0 d';
  if (days > 0) return `+${days} d`;
  return `${days} d`;
}

export function formatEndereco(p: {
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  cep?: string;
}): string {
  const linha1 = [p.logradouro, p.numero].filter(Boolean).join(' ');
  const extra = p.complemento ? `, ${p.complemento}` : '';
  const linha2 = [p.bairro, p.cidade, p.uf, p.cep].filter(Boolean).join(' ');
  return [linha1 + extra, linha2].filter((s) => s.trim()).join('\n');
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

export function parseHHMM(value: string): { h: number; m: number } {
  const [h, m] = (value || '').slice(0, 5).split(':').map(Number);
  return {
    h: Number.isFinite(h) ? h : 8,
    m: Number.isFinite(m) ? m : 0,
  };
}

export function slotTimesFromConfig(horaInicio = '08:00', horaFim = '18:00', stepMin = 15): string[] {
  const start = parseHHMM(horaInicio);
  const end = parseHHMM(horaFim);
  const step = stepMin > 0 ? stepMin : 15;
  const out: string[] = [];
  let minutes = start.h * 60 + start.m;
  const endMinutes = end.h * 60 + end.m;
  while (minutes < endMinutes) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    out.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`);
    minutes += step;
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
  if (status === 'checkin') return { bg: '#BBDEFB', border: '#1E88E5' };
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

export function formatBRL(value: string | number | null | undefined): string {
  const n = typeof value === 'number' ? value : Number(String(value || '0').replace(',', '.'));
  if (!Number.isFinite(n)) return 'R$ 0,00';
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function alertaAlergia(alergias: string, medicamento: string): boolean {
  const med = (medicamento || '').trim().toLowerCase();
  if (!med) return false;
  return (alergias || '')
    .replace(/;/g, ',')
    .split(',')
    .map((t) => t.trim().toLowerCase())
    .filter((t) => t.length > 2)
    .some((t) => med.includes(t) || t.includes(med));
}

export function minutosTeleRestantes(usados: number, teto = 600): number {
  return Math.max(0, teto - (usados || 0));
}

export function whatsappHref(phone: string): string | null {
  const d = (phone || '').replace(/\D/g, '');
  if (d.length < 10) return null;
  const withCountry = d.startsWith('55') ? d : `55${d}`;
  return `https://wa.me/${withCountry}`;
}
