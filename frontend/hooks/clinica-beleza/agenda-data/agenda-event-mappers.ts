import {
  CLINICA_AGENDA_BLOQUEIO_COLORS,
  CLINICA_AGENDA_STATUS_COLORS,
  getAgendaStatusColor,
  type AgendaStatusColorMap,
} from "@/lib/clinica-beleza-constants";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { BloqueioHorario } from "@/lib/clinica-beleza-entities";
import { entityName } from "@/lib/clinica-beleza-entities";
import type {
  ClinicaPatient,
  ClinicaProcedure,
  ClinicaProfessional,
  HorarioTrabalhoRow,
} from "@/lib/clinica-beleza-entities";
import { intervalosEventsFromHorarios } from "@/lib/clinica-beleza-work-hours";

export function formatarAgendaEvento(
  e: AgendaEventData | Record<string, unknown>,
  comRestricaoExpediente: boolean,
  statusColors: AgendaStatusColorMap = CLINICA_AGENDA_STATUS_COLORS,
): AgendaEventData {
  const raw = e as Record<string, unknown>;
  const status = String(raw.status ?? "");
  const cores = getAgendaStatusColor(status, statusColors);
  const titulo =
    [raw.patient_name, raw.procedure_name].filter(Boolean).join(" • ") ||
    String(raw.title ?? "") ||
    "Agendamento";
  return {
    id: String(raw.id),
    title: titulo,
    start: String(raw.start),
    end: String(raw.end),
    backgroundColor: cores.bg,
    borderColor: cores.border,
    textColor: "#fff",
    ...(comRestricaoExpediente ? { constraint: "businessHours" as const } : {}),
    extendedProps: {
      dbId: raw.id as string | number,
      status,
      patient_name: String(raw.patient_name ?? ""),
      patient_phone: String(raw.patient_phone ?? ""),
      professional_name: String(raw.professional_name ?? ""),
      procedure_name: String(raw.procedure_name ?? ""),
      procedure_duration: raw.procedure_duration as number | undefined,
      duracao_minutos: raw.duracao_minutos as number | undefined,
      procedure_price: raw.procedure_price as string | undefined,
      notes: String(raw.notes ?? ""),
      version: raw.version as number | undefined,
      updated_at: raw.updated_at as string | undefined,
    },
  };
}

export function agendaEventsEqual(a: AgendaEventData[], b: AgendaEventData[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    const x = a[i];
    const y = b[i];
    if (
      x.id !== y.id ||
      x.start !== y.start ||
      x.end !== y.end ||
      x.title !== y.title ||
      x.backgroundColor !== y.backgroundColor
    ) {
      return false;
    }
    if (x.extendedProps?.status !== y.extendedProps?.status) return false;
  }
  return true;
}

export function bloqueiosToAgendaEvents(bloqueiosList: BloqueioHorario[]): AgendaEventData[] {
  return bloqueiosList.map((b) => {
    const rawS = b.data_inicio ?? "";
    const rawE = b.data_fim ?? "";
    const hasT =
      typeof rawS === "string" &&
      rawS.includes("T") &&
      typeof rawE === "string" &&
      rawE.includes("T");
    const startStr = hasT ? rawS : (rawS.slice(0, 10) ? `${rawS.slice(0, 10)}T00:00:00` : "");
    const endStr = hasT ? rawE : (rawS.slice(0, 10) ? `${rawS.slice(0, 10)}T23:59:59` : "");
    return {
      id: `bloqueio-${b.id}`,
      title: `🚫 ${b.motivo}`,
      start: startStr,
      end: endStr,
      allDay: false,
      backgroundColor: CLINICA_AGENDA_BLOQUEIO_COLORS.bg,
      borderColor: CLINICA_AGENDA_BLOQUEIO_COLORS.border,
      textColor: "#fff",
      editable: true,
      durationEditable: true,
      startEditable: true,
      classNames: ["fc-event-bloqueio"],
      extendedProps: {
        isBloqueio: true,
        bloqueioId: b.id,
        motivo: b.motivo,
        professional: b.professional,
        professional_name: b.professional_name || "Todos",
      },
    } as AgendaEventData;
  });
}

export function temExpedienteProfissional(
  selectedProfessional: string,
  horariosTrabalho: HorarioTrabalhoRow[],
): boolean {
  return Boolean(selectedProfessional && horariosTrabalho.some((h) => h.ativo));
}

export function intervalosAgendaProfissional(
  selectedProfessional: string,
  horariosTrabalho: HorarioTrabalhoRow[],
  professionals: ClinicaProfessional[],
): AgendaEventData[] {
  if (!selectedProfessional || horariosTrabalho.length === 0) return [];
  const profName =
    entityName(professionals.find((p) => p.id === Number(selectedProfessional)) || {}) ||
    "Profissional";
  return intervalosEventsFromHorarios(selectedProfessional, horariosTrabalho, profName);
}

export function buildPendingSyncEvents({
  fila,
  patients,
  procedures,
  professionals,
  temExpediente,
  statusColors = CLINICA_AGENDA_STATUS_COLORS,
}: {
  fila: { id: number; tipo: string; payload: unknown }[];
  patients: ClinicaPatient[];
  procedures: ClinicaProcedure[];
  professionals: ClinicaProfessional[];
  temExpediente: boolean;
  statusColors?: AgendaStatusColorMap;
}): AgendaEventData[] {
  return fila
    .filter((f) => f.tipo === "agendamento")
    .map((item) => {
      const p = item.payload as Record<string, unknown>;
      const date = p.date ? new Date(String(p.date)) : new Date();
      const patient = patients.find((x) => x.id === p.patient);
      const procedure = procedures.find((x) => x.id === p.procedure);
      const professional = professionals.find((x) => x.id === p.professional);
      const duration = procedure?.duration ?? 30;
      const endDate = new Date(date);
      endDate.setMinutes(endDate.getMinutes() + duration);
      const status = String(p.status || "SCHEDULED");
      const cores = getAgendaStatusColor(status, statusColors);
      return {
        id: `offline-${item.id}`,
        title:
          [entityName(patient || {}), entityName(procedure || {})].filter(Boolean).join(" • ") ||
          "Agendamento (pendente sync)",
        start: date.toISOString(),
        end: endDate.toISOString(),
        backgroundColor: cores.bg,
        borderColor: cores.border,
        textColor: "#fff",
        ...(temExpediente ? { constraint: "businessHours" as const } : {}),
        extendedProps: {
          dbId: `offline-${item.id}`,
          status,
          patient_name: entityName(patient || {}),
          patient_phone: "",
          professional_name: professional?.name ?? "",
          procedure_name: entityName(procedure || {}),
          procedure_duration: duration,
          procedure_price: String(procedure?.price ?? ""),
          notes: String(p.notes ?? ""),
        },
      } as AgendaEventData;
    });
}

export function buildEventosOnline({
  rawEvents,
  bloqueios,
  horariosTrabalho,
  professionals,
  selectedProfessional,
  pendingEvents,
  statusColors = CLINICA_AGENDA_STATUS_COLORS,
}: {
  rawEvents: Record<string, unknown>[];
  bloqueios: BloqueioHorario[];
  horariosTrabalho: HorarioTrabalhoRow[];
  professionals: ClinicaProfessional[];
  selectedProfessional: string;
  pendingEvents: AgendaEventData[];
  statusColors?: AgendaStatusColorMap;
}): AgendaEventData[] {
  const temExpediente = temExpedienteProfissional(selectedProfessional, horariosTrabalho);
  const eventosFormatados = rawEvents.map((ev) =>
    formatarAgendaEvento(ev, temExpediente, statusColors),
  );
  const bloqueiosAsEvents = bloqueiosToAgendaEvents(bloqueios);
  const intervalos = intervalosAgendaProfissional(
    selectedProfessional,
    horariosTrabalho,
    professionals,
  );
  return [...eventosFormatados, ...bloqueiosAsEvents, ...intervalos, ...pendingEvents];
}
