import { formatApiErrorBody } from "@/lib/api-errors";
import { ClinicaBelezaAPI, clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { buildQuickPatientBody, extractQuickPatientError } from "./criar-agendamento-submit-utils";

export async function createQuickPatient(data: {
  nome: string;
  telefone: string;
  cpf: string;
}): Promise<unknown> {
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
  payload: Record<string, unknown>,
): Promise<{ id?: number } | null> {
  return ClinicaBelezaAPI.consultas.criar(
    payload as {
      patient: number;
      professional: number;
      procedure?: number;
      procedures_ids?: number[];
      local_atendimento?: number;
      convenio?: number | null;
    },
  );
}

export async function submitAgendamentoOnline(payload: Record<string, unknown>): Promise<void> {
  const res = await clinicaBelezaFetch("/agenda/create/", {
    method: "POST",
    body: JSON.stringify({ ...payload, status: "SCHEDULED" }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(formatApiErrorBody(data) || "Erro ao criar agendamento");
  }
}
