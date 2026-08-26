import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { parseEventDate } from "@/lib/clinica-beleza-datetime";
import { entityName, professionalSpecialty, type ClinicaProfessional } from "@/lib/clinica-beleza-entities";

export const AGENDA_DIA_CORES = [
  "#0d9488",
  "#2563eb",
  "#7c3aed",
  "#db2777",
  "#ea580c",
  "#0891b2",
] as const;

const PARTICULAS = new Set(["DE", "DA", "DO", "DOS", "DAS", "E", "DR", "DRA"]);

export function iniciaisProfissional(nome: string): string {
  const palavras = nome
    .replace(/\./g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .filter((p) => !PARTICULAS.has(p.toUpperCase()));
  const base = palavras.length ? palavras : nome.trim().split(/\s+/).filter(Boolean);
  if (base.length === 0) return "?";
  if (base.length === 1) return base[0].slice(0, 2).toUpperCase();
  return `${base[0][0]}${base[1][0]}`.toUpperCase();
}

export function corProfissionalAgenda(id: number): string {
  return AGENDA_DIA_CORES[Math.abs(id) % AGENDA_DIA_CORES.length];
}

export function toAgendaDiaIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function addDaysIso(iso: string, delta: number): string {
  const [y, mo, d] = iso.split("-").map(Number);
  const dt = new Date(y, (mo || 1) - 1, d || 1);
  dt.setDate(dt.getDate() + delta);
  return toAgendaDiaIso(dt);
}

export function parseHmToMinutes(t: string): number {
  const [h, m] = (t || "07:00:00").slice(0, 5).split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

export function minutesToHm(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function sameDayIso(date: Date, iso: string): boolean {
  return toAgendaDiaIso(date) === iso;
}

export function eventProfessionalId(evt: AgendaEventData): number | null {
  const raw = evt.extendedProps?.professional;
  if (raw == null || raw === "") return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export type AgendaDiaProfissionalColuna = {
  id: number;
  nome: string;
  especialidade: string;
  iniciais: string;
  cor: string;
};

export function colunasProfissionaisDia(
  professionals: ClinicaProfessional[],
  selectedProfessional: string,
): AgendaDiaProfissionalColuna[] {
  const lista = selectedProfessional
    ? professionals.filter((p) => String(p.id) === selectedProfessional)
    : professionals;
  return lista.map((p) => {
    const nome = entityName(p) || `Profissional ${p.id}`;
    return {
      id: p.id,
      nome,
      especialidade: professionalSpecialty(p),
      iniciais: iniciaisProfissional(nome),
      cor: corProfissionalAgenda(p.id),
    };
  });
}

export type AgendaDiaItem = { evt: AgendaEventData; start: Date; end: Date };

export function eventosDoDiaNaColuna(
  eventos: AgendaEventData[],
  dateIso: string,
  professionalId: number,
): AgendaDiaItem[] {
  const out: AgendaDiaItem[] = [];
  for (const evt of eventos) {
    const start = parseEventDate(evt.start);
    if (!start || !sameDayIso(start, dateIso)) continue;
    const end = parseEventDate(evt.end) || start;
    const pid = eventProfessionalId(evt);
    const global = pid == null && Boolean(evt.extendedProps?.isBloqueio);
    if (pid !== professionalId && !global) continue;
    out.push({ evt, start, end });
  }
  return out.sort((a, b) => a.start.getTime() - b.start.getTime());
}

export function eventosDoDia(eventos: AgendaEventData[], dateIso: string): AgendaDiaItem[] {
  const out: AgendaDiaItem[] = [];
  for (const evt of eventos) {
    if (evt.extendedProps?.isIntervalo || evt.extendedProps?.isBloqueio) continue;
    const start = parseEventDate(evt.start);
    if (!start || !sameDayIso(start, dateIso)) continue;
    const end = parseEventDate(evt.end) || start;
    out.push({ evt, start, end });
  }
  return out.sort((a, b) => a.start.getTime() - b.start.getTime());
}

export function tituloMesCalendario(iso: string): string {
  const [y, mo] = iso.split("-").map(Number);
  return new Date(y, (mo || 1) - 1, 1).toLocaleDateString("pt-BR", {
    month: "long",
    year: "numeric",
  });
}

export function celulasCalendarioMes(iso: string): { iso: string; inMonth: boolean }[] {
  const [y, mo] = iso.split("-").map(Number);
  const first = new Date(y, (mo || 1) - 1, 1);
  const start = new Date(first);
  start.setDate(1 - first.getDay());
  const cells: { iso: string; inMonth: boolean }[] = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    cells.push({
      iso: toAgendaDiaIso(d),
      inMonth: d.getMonth() === first.getMonth(),
    });
  }
  return cells;
}

export function snapMinutos(totalMin: number, snap = 5): number {
  return Math.round(totalMin / snap) * snap;
}

export function slotDateFromMinutes(iso: string, minutesFromMidnight: number): Date {
  const [y, mo, d] = iso.split("-").map(Number);
  const dt = new Date(y, (mo || 1) - 1, d || 1, 0, 0, 0, 0);
  dt.setMinutes(minutesFromMidnight);
  return dt;
}
