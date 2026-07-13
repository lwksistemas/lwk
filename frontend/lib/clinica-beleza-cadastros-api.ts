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
}

const CADASTRO_PAGE_SIZE = 200;
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
    page: 1,
    page_size: CADASTRO_PAGE_SIZE,
    active: true,
  });
}

/** Profissionais visíveis na agenda (filtro scheduling=true no backend). */
export async function fetchClinicaSchedulingProfessionals(): Promise<ClinicaProfessionalOption[]> {
  return ClinicaBelezaAPI.getList<ClinicaProfessionalOption>("/professionals/", {
    page: 1,
    page_size: CADASTRO_PAGE_SIZE,
    scheduling: true,
  });
}

export async function fetchClinicaAgendaPatients() {
  return ClinicaBelezaAPI.getList("/patients/", {
    page: 1,
    page_size: 500,
    active: true,
  });
}

export async function fetchClinicaAgendaEvents(professionalId: string): Promise<AgendaEventData[]> {
  const path = professionalId ? `/agenda/?professional=${professionalId}` : "/agenda/";
  const res = await clinicaBelezaFetch(path);
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
    page: 1,
    page_size: CADASTRO_PAGE_SIZE,
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
