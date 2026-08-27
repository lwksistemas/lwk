import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { getAgendaStatusLabelCurto } from "@/lib/clinica-beleza-constants";
import { arredondarDuracaoAgendaMin, parseEventDate } from "@/lib/clinica-beleza-datetime";
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

export type FamiliaBloqueioAgenda = "ferias" | "manutencao" | "evento" | "reuniao" | "outro";

/** Agrupa o motivo livre (Férias, Reunião videomaker, etc.) para cor e selo. */
export function familiaBloqueioAgenda(motivo?: string): FamiliaBloqueioAgenda {
  const t = (motivo || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  if (t.includes("ferias")) return "ferias";
  if (t.includes("manutenc")) return "manutencao";
  if (t.includes("evento")) return "evento";
  if (t.includes("reuniao")) return "reuniao";
  return "outro";
}

/** Cores de bloqueio longe do roxo Aguardando e do verde Presente. */
export const COR_BLOQUEIO_AGENDA: Record<FamiliaBloqueioAgenda, string> = {
  ferias: "#0f766e",
  manutencao: "#475569",
  evento: "#0c4a6e",
  reuniao: "#44403c",
  outro: "#57534e",
};

export function corBloqueioAgenda(motivo?: string): string {
  return COR_BLOQUEIO_AGENDA[familiaBloqueioAgenda(motivo)];
}

export function rotuloTipoBloqueioAgenda(motivo?: string): string {
  const familia = familiaBloqueioAgenda(motivo);
  if (familia === "ferias") return "Férias";
  if (familia === "manutencao") return "Manutenção";
  if (familia === "evento") return "Evento";
  if (familia === "reuniao") return "Reunião";
  return "Bloqueio";
}

/** Cor do card = status do agendamento (não a cor da coluna do profissional). */
export function corStatusEventoAgenda(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isIntervalo) return "#d97706";
  if (p.isBloqueio) return corBloqueioAgenda(p.motivo);
  return evt.backgroundColor || evt.borderColor || "#a855f7";
}

export function fundoPastelAgenda(hex: string, pct = 28): string {
  return `color-mix(in srgb, ${hex} ${pct}%, white)`;
}

export function rotuloStatusCardAgenda(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isBloqueio) return rotuloTipoBloqueioAgenda(p.motivo);
  if (p.isIntervalo) return "Intervalo";
  return getAgendaStatusLabelCurto(String(p.status || "SCHEDULED"));
}

export type EstiloCardAgenda = {
  cor: string;
  backgroundColor: string;
  borderLeft: string;
  backgroundImage?: string;
};

export function estiloCardStatusAgenda(evt: AgendaEventData): EstiloCardAgenda {
  const p = evt.extendedProps || {};
  const cor = corStatusEventoAgenda(evt);
  if (p.isBloqueio) {
    return {
      cor,
      backgroundColor: fundoPastelAgenda(cor, 14),
      borderLeft: `4px dashed ${cor}`,
      backgroundImage:
        `repeating-linear-gradient(-45deg, color-mix(in srgb, ${cor} 18%, transparent) 0 6px, transparent 6px 12px)`,
    };
  }
  return {
    cor,
    backgroundColor: fundoPastelAgenda(cor),
    borderLeft: `4px solid ${cor}`,
  };
}

export function estiloInlineCardAgenda(evt: AgendaEventData): {
  backgroundColor: string;
  borderLeft: string;
  backgroundImage?: string;
} {
  const e = estiloCardStatusAgenda(evt);
  return {
    backgroundColor: e.backgroundColor,
    borderLeft: e.borderLeft,
    ...(e.backgroundImage ? { backgroundImage: e.backgroundImage } : {}),
  };
}

export function capitalizarAgenda(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

export function tituloCardAgenda(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isBloqueio) return (p.motivo || evt.title).replace(/^🚫\s*/, "");
  if (p.isIntervalo) return evt.title.replace(/^🍽️\s*/, "") || "Intervalo / Almoço";
  return (p.patient_name || evt.title).toUpperCase();
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

export function combinarDiaEHorario(dateIso: string, source: Date): Date {
  return slotDateFromMinutes(
    dateIso,
    source.getHours() * 60 + source.getMinutes(),
  );
}

export function duracaoEventoMinutos(evt: AgendaEventData, start: Date, end: Date): number {
  const raw = evt.extendedProps?.duracao_minutos ?? evt.extendedProps?.procedure_duration;
  if (typeof raw === "number" && raw > 0) return raw;
  return Math.max(5, Math.round((end.getTime() - start.getTime()) / 60000));
}

export function minutosArrastoNaGrade(
  clientY: number,
  gridTop: number,
  minMin: number,
  pxPerMin: number,
  offsetY = 0,
): number {
  return snapMinutos(minMin + (clientY - offsetY - gridTop) / pxPerMin);
}

export function clampMinutosInicio(
  minutes: number,
  minMin: number,
  maxMin: number,
  durationMin: number,
): number {
  const teto = Math.max(minMin, maxMin - durationMin);
  return Math.min(Math.max(minutes, minMin), teto);
}

export function duracaoResizeNaGrade(
  startMin: number,
  clientY: number,
  gridTop: number,
  minMin: number,
  maxMin: number,
  pxPerMin: number,
): number {
  const endMin = Math.min(maxMin, Math.max(startMin + 5, snapMinutos(minMin + (clientY - gridTop) / pxPerMin)));
  return arredondarDuracaoAgendaMin(endMin - startMin);
}

export function mesmoHorarioLocal(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate() &&
    a.getHours() === b.getHours() &&
    a.getMinutes() === b.getMinutes()
  );
}

export function movimentoGradeAlterou(
  evt: AgendaEventData,
  start: Date,
  professionalId: number,
): boolean {
  const oldStart = parseEventDate(evt.start);
  const oldPid = eventProfessionalId(evt);
  if (oldPid !== professionalId) return true;
  if (!oldStart) return true;
  return !mesmoHorarioLocal(oldStart, start);
}

export function inicioSemanaIso(iso: string): string {
  const [y, mo, d] = iso.split("-").map(Number);
  const dt = new Date(y, (mo || 1) - 1, d || 1);
  const weekday = dt.getDay();
  const delta = weekday === 0 ? -6 : 1 - weekday;
  dt.setDate(dt.getDate() + delta);
  return toAgendaDiaIso(dt);
}

export function diasSemanaIso(iso: string, hiddenDays: number[] = [0]): string[] {
  const start = inicioSemanaIso(iso);
  const out: string[] = [];
  for (let i = 0; i < 7; i++) {
    const dayIso = addDaysIso(start, i);
    const [y, mo, d] = dayIso.split("-").map(Number);
    const jsDay = new Date(y, (mo || 1) - 1, d || 1).getDay();
    if (hiddenDays.includes(jsDay)) continue;
    out.push(dayIso);
  }
  return out.length ? out : [start];
}

export function eventosDoDiaFiltrados(
  eventos: AgendaEventData[],
  dateIso: string,
  selectedProfessional: string,
): AgendaDiaItem[] {
  const lista = eventosDoDia(eventos, dateIso);
  if (!selectedProfessional) return lista;
  return lista.filter((row) => {
    const pid = eventProfessionalId(row.evt);
    if (pid == null && Boolean(row.evt.extendedProps?.isBloqueio)) return true;
    return String(pid) === selectedProfessional;
  });
}

export const AGENDA_COLUNA_MIN = 160;
export const AGENDA_COLUNA_MAX = 560;

export function clampLarguraColuna(
  px: number,
  min = AGENDA_COLUNA_MIN,
  max = AGENDA_COLUNA_MAX,
): number {
  return Math.min(max, Math.max(min, Math.round(px)));
}

const STATUS_AGENDA_FORA_DA_FILA = new Set(["CANCELLED", "NO_SHOW", "COMPLETED"]);

export function ehAgendamentoCliente(evt: AgendaEventData): boolean {
  const p = evt.extendedProps || {};
  return !p.isBloqueio && !p.isIntervalo;
}

export function primeiroNomeProfissional(nome: string | undefined): string {
  if (!nome) return "";
  const palavras = nome
    .replace(/\./g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .filter((p) => !PARTICULAS.has(p.toUpperCase()));
  return palavras[0] || nome.trim();
}

export function agendamentoEmAndamento(item: AgendaDiaItem, now: Date): boolean {
  return item.start.getTime() <= now.getTime() && item.end.getTime() > now.getTime();
}

/**
 * Fila da recepção no painel direito: do horário atual em diante no dia
 * selecionado, todos os profissionais (ou o filtro do topo).
 */
export function proximosAgendamentosAgenda(
  eventos: AgendaEventData[],
  dateIso: string,
  now: Date = new Date(),
  selectedProfessional = "",
): AgendaDiaItem[] {
  const hojeIso = toAgendaDiaIso(now);
  return eventosDoDiaFiltrados(eventos, dateIso, selectedProfessional).filter((row) => {
    if (!ehAgendamentoCliente(row.evt)) return false;
    const status = String(row.evt.extendedProps?.status || "SCHEDULED").toUpperCase();
    if (STATUS_AGENDA_FORA_DA_FILA.has(status)) return false;
    if (dateIso === hojeIso && row.end.getTime() <= now.getTime()) return false;
    return true;
  });
}

export function faixasSobrepostas(
  items: AgendaDiaItem[],
): { item: AgendaDiaItem; lane: number; lanes: number }[] {
  const sorted = [...items].sort((a, b) => a.start.getTime() - b.start.getTime());
  const assigned: { item: AgendaDiaItem; lane: number }[] = [];
  const active: { end: number; lane: number }[] = [];
  for (const item of sorted) {
    const start = item.start.getTime();
    for (let i = active.length - 1; i >= 0; i--) {
      if (active[i].end <= start) active.splice(i, 1);
    }
    const used = new Set(active.map((a) => a.lane));
    let lane = 0;
    while (used.has(lane)) lane += 1;
    active.push({ end: item.end.getTime(), lane });
    assigned.push({ item, lane });
  }
  return assigned.map((row) => {
    const overlapping = assigned.filter(
      (o) => o.item.start < row.item.end && o.item.end > row.item.start,
    );
    const lanes = overlapping.reduce((max, o) => Math.max(max, o.lane + 1), 1);
    return { item: row.item, lane: row.lane, lanes };
  });
}
