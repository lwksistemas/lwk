/**
 * Busca paginada de cadastros — Clínica da Beleza (pacientes, procedimentos, etc.).
 */
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import {
  ClinicaBelezaAPI,
  clinicaBelezaFetch,
  type LocalAtendimentoItem,
  type NomeAgendaItem,
} from "@/lib/clinica-beleza-api";

export interface ClinicaProfessionalOption {
  id: number;
  name?: string;
  nome?: string;
  especialidade?: string;
  specialty?: string;
  foto_url?: string | null;
}

const PATIENT_SEARCH_PAGE_SIZE = 40;
const HISTORICO_PAGE_SIZE = 100;

export const clinicaBelezaQueryKeys = {
  professionals: () => ["clinica-beleza", "professionals"] as const,
  schedulingProfessionals: () => ["clinica-beleza", "professionals", "scheduling"] as const,
  procedures: (categoria?: string) => ["clinica-beleza", "procedures", categoria ?? "all"] as const,
  nomesAgenda: () => ["clinica-beleza", "nomes-agenda"] as const,
  locaisAtendimento: () => ["clinica-beleza", "locais-atendimento"] as const,
  patientSearch: (q: string) => ["clinica-beleza", "patients-search", q] as const,
  historicoPaciente: (patientId: number) => ["clinica-beleza", "historico-paciente", patientId] as const,
  agendaPatients: () => ["clinica-beleza", "patients", "agenda"] as const,
  agendaEvents: (professionalId: string) => ["clinica-beleza", "agenda-events", professionalId] as const,
  agendaBloqueios: (professionalId: string) => ["clinica-beleza", "agenda-bloqueios", professionalId] as const,
  horariosTrabalho: (professionalId: string) => ["clinica-beleza", "horarios-trabalho", professionalId] as const,
};

export async function fetchClinicaProfessionals(): Promise<ClinicaProfessionalOption[]> {
  return ClinicaBelezaAPI.getList<ClinicaProfessionalOption>("/professionals/", {
    all: 1,
    active: true,
  });
}

/** Profissionais visíveis na agenda (filtro scheduling=true no backend). */
export async function fetchClinicaSchedulingProfessionals(): Promise<ClinicaProfessionalOption[]> {
  return ClinicaBelezaAPI.getList<ClinicaProfessionalOption>("/professionals/", {
    all: 1,
    scheduling: true,
  });
}

function ymdLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function parseYmdLocal(iso: string): Date {
  const [y, mo, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(y, (mo || 1) - 1, d || 1);
}

export type AgendaFetchRange = { start: string; end: string };

/** Janela inicial enxuta: 21 dias atrás ↔ 45 à frente. */
export function defaultAgendaFetchRange(now = new Date()): AgendaFetchRange {
  return {
    start: ymdLocal(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 21)),
    end: ymdLocal(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 45)),
  };
}

let agendaFetchRange: AgendaFetchRange = defaultAgendaFetchRange();

export function getAgendaFetchRange(): AgendaFetchRange {
  return agendaFetchRange;
}

/** Só testes — redefine a janela sem tocar na API. */
export function resetAgendaFetchRange(range?: AgendaFetchRange, now = new Date()): void {
  agendaFetchRange = range ?? defaultAgendaFetchRange(now);
}

/**
 * Alinha a janela da API ao período visível. Retorna true se a próxima busca deve refetch.
 */
export function syncAgendaFetchRangeToVisible(visibleStart: string, visibleEnd: string): boolean {
  const vs = parseYmdLocal(visibleStart);
  const ve = parseYmdLocal(visibleEnd);
  if (Number.isNaN(vs.getTime()) || Number.isNaN(ve.getTime())) return false;

  const curS = parseYmdLocal(agendaFetchRange.start);
  const curE = parseYmdLocal(agendaFetchRange.end);
  const margemMs = 3 * 86400000;
  if (vs.getTime() >= curS.getTime() + margemMs && ve.getTime() <= curE.getTime() - margemMs) {
    return false;
  }

  const pad = 14;
  const nextStart = new Date(vs.getFullYear(), vs.getMonth(), vs.getDate() - pad);
  let nextEnd = new Date(ve.getFullYear(), ve.getMonth(), ve.getDate() + pad);
  const maxSpan = 120;
  if ((nextEnd.getTime() - nextStart.getTime()) / 86400000 > maxSpan) {
    nextEnd = new Date(nextStart.getTime() + maxSpan * 86400000);
  }
  const next = { start: ymdLocal(nextStart), end: ymdLocal(nextEnd) };
  if (next.start === agendaFetchRange.start && next.end === agendaFetchRange.end) return false;
  agendaFetchRange = next;
  return true;
}

export async function fetchClinicaAgendaEvents(professionalId: string): Promise<AgendaEventData[]> {
  const params = new URLSearchParams();
  params.set("start", agendaFetchRange.start);
  params.set("end", agendaFetchRange.end);
  if (professionalId) params.set("professional", professionalId);
  const res = await clinicaBelezaFetch(`/agenda/?${params.toString()}`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchClinicaAgendaBloqueios(professionalId: string) {
  const path = professionalId ? `/bloqueios/?professional=${professionalId}` : "/bloqueios/";
  const res = await clinicaBelezaFetch(path);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchClinicaHorariosTrabalho(professionalId: string) {
  if (!professionalId) return [];
  const res = await clinicaBelezaFetch(`/professionals/${professionalId}/horarios-trabalho/`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchClinicaProcedures(categoria?: string): Promise<ConsultaFormProcedure[]> {
  const params: Record<string, string | number | boolean> = {
    all: 1,
    active: true,
  };
  if (categoria) params.categoria = categoria;
  return ClinicaBelezaAPI.getList<ConsultaFormProcedure>("/procedures/", params);
}

export async function fetchClinicaNomesAgenda(): Promise<NomeAgendaItem[]> {
  const data = await ClinicaBelezaAPI.nomesAgenda.list();
  return Array.isArray(data) ? data : [];
}

export async function fetchClinicaLocaisAtendimento(): Promise<LocalAtendimentoItem[]> {
  const data = await ClinicaBelezaAPI.locaisAtendimento.list();
  return Array.isArray(data) ? data : [];
}

export async function searchClinicaPatients(query: string): Promise<PatientQuickOption[]> {
  const q = query.trim();
  if (q.length < 1) return [];
  return ClinicaBelezaAPI.getList<PatientQuickOption>("/patients/", {
    page: 1,
    page_size: PATIENT_SEARCH_PAGE_SIZE,
    active: true,
    search: q,
  });
}

export async function searchClinicaProcedures(query: string, categoria?: string): Promise<ConsultaFormProcedure[]> {
  const q = query.trim();
  const params: Record<string, string | number | boolean> = {
    page: 1,
    page_size: PATIENT_SEARCH_PAGE_SIZE,
    active: true,
  };
  if (categoria) params.categoria = categoria;
  if (q.length >= 2) params.search = q;
  return ClinicaBelezaAPI.getList<ConsultaFormProcedure>("/procedures/", params);
}

export async function fetchHistoricoPaciente(patientId: number): Promise<Consulta[]> {
  return ClinicaBelezaAPI.getList<Consulta>(`/patients/${patientId}/consultas/`, {
    page: 1,
    page_size: HISTORICO_PAGE_SIZE,
  });
}
