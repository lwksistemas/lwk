import { formatApiErrorBody } from "@/lib/api-errors";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { buildQuickPatientBody, extractQuickPatientError } from "./criar-agendamento-submit-utils";
import type { CriarAgendamentoPayload } from "./criar-agendamento-builders";

export async function createQuickPatient(data: {
  nome: string;
  telefone: string;
  cpf: string;
}): Promise<PatientQuickOption> {
  const res = await clinicaBelezaFetch("/patients/", {
    method: "POST",
    body: JSON.stringify(buildQuickPatientBody(data)),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(extractQuickPatientError(err));
  }
  return res.json();
}

export async function submitConsultaOnline(
  payload: CriarAgendamentoPayload,
): Promise<{ id?: number } | null> {
  return ClinicaBelezaAPI.consultas.criar(payload);
}

export async function submitProtocoloPersonalizado(input: {
  contratoId: number;
  professionalId: number;
  localId: number | "";
  date: Date;
}): Promise<{ agendamentos: Array<{ ajustado?: boolean }> }> {
  const res = await clinicaBelezaFetch(`/protocolos/personalizados/${input.contratoId}/agendar/`, {
    method: "POST",
    body: JSON.stringify({
      professional: input.professionalId,
      local_atendimento: input.localId || undefined,
      data_inicio: input.date.toISOString(),
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(formatApiErrorBody(data) || "Erro ao agendar o protocolo");
  }
  return data;
}

export async function submitAgendamentoOnline(payload: CriarAgendamentoPayload): Promise<void> {
  const res = await clinicaBelezaFetch("/agenda/create/", {
    method: "POST",
    body: JSON.stringify({ ...payload, status: "SCHEDULED" }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(formatApiErrorBody(data) || "Erro ao criar agendamento");
  }
}
