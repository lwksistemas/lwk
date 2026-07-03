import type { PatientQuickOption } from "@/components/clinica-beleza/PatientQuickRegisterField";
import type { CriarAgendamentoProfessional } from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { ConsultaFormProcedure } from "@/hooks/clinica-beleza/useNovaConsultaForm";
import { notificarFilaAtualizada } from "@/hooks/useSyncPending";
import type { NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";
import { adicionarNaFilaSync } from "@/lib/offline-db";

export async function enqueueConsultaOffline(payload: Record<string, unknown>) {
  await adicionarNaFilaSync({ tipo: "consulta", payload });
  notificarFilaAtualizada();
}

export async function enqueueAgendamentoOffline(payload: Record<string, unknown>) {
  await adicionarNaFilaSync({ tipo: "agendamento", payload: { ...payload, status: "SCHEDULED" } });
  notificarFilaAtualizada();
}

export function buildOfflineAgendaEvent({
  date,
  duracaoMinutos,
  patientId,
  professionalId,
  selectedProcedures,
  agendaId,
  notes,
  patients,
  professionals,
  procedures,
  nomesAgenda,
  resumoValor,
  resumoDuracao,
}: {
  date: Date;
  duracaoMinutos: number;
  patientId: number | "";
  professionalId: number | "";
  selectedProcedures: number[];
  agendaId: number;
  notes: string;
  patients: PatientQuickOption[];
  professionals: CriarAgendamentoProfessional[];
  procedures: ConsultaFormProcedure[];
  nomesAgenda: NomeAgendaItem[];
  resumoValor: number;
  resumoDuracao: number;
}) {
  const patient = patients.find((p) => p.id === patientId);
  const professional = professionals.find((p) => p.id === professionalId);
  const procNames = selectedProcedures
    .map((id) => entityName(procedures.find((p) => p.id === id) || {}))
    .filter(Boolean)
    .join(", ");
  const nomeAgenda = nomesAgenda.find((a) => a.id === agendaId)?.nome;
  const titulo =
    [entityName(patient || {}), procNames || nomeAgenda || "Atendimento"].filter(Boolean).join(" • ") ||
    "Agendamento (offline)";
  const tempId = `offline-${Date.now()}`;
  const endDate = new Date(date);
  endDate.setMinutes(endDate.getMinutes() + duracaoMinutos);

  return {
    id: tempId,
    title: titulo,
    start: date.toISOString(),
    end: endDate.toISOString(),
    backgroundColor: "#a855f7",
    borderColor: "#9333ea",
    textColor: "#fff",
    extendedProps: {
      dbId: tempId,
      status: "SCHEDULED",
      patient_name: entityName(patient || {}),
      patient_phone: "",
      professional_name: entityName(professional || {}),
      procedure_name: procNames,
      procedure_duration: resumoDuracao,
      procedure_price: resumoValor,
      notes: notes.trim() || "",
    },
  };
}
