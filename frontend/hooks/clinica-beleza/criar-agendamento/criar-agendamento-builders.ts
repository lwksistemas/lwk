import type { RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";
import type { LocalAtendimentoItem } from "@/lib/clinica-beleza-api";

export function buildAppointmentDate(
  dateInput: string,
  time: string,
  selectedDate: Date | null,
): Date | null {
  const dateSource = dateInput ? new Date(`${dateInput}T12:00:00`) : selectedDate;
  if (!dateSource) return null;
  const [h, m] = time.split(":").map(Number);
  const date = new Date(dateSource);
  date.setHours(h, m, 0, 0);
  return date;
}

export function buildCriarAgendamentoPayload({
  patientId,
  agendaId,
  notes,
  date,
  professionalId,
  localId,
  convenioId,
  selectedProcedures,
  retornoProcedureId,
}: {
  patientId: number | "";
  agendaId: number;
  notes: string;
  date: Date;
  professionalId: number | "";
  localId: number | "";
  convenioId: number | "";
  selectedProcedures: number[];
  retornoProcedureId: number | "";
}): Record<string, unknown> {
  const basePayload: Record<string, unknown> = {
    patient: Number(patientId),
    nome_agenda: Number(agendaId),
    notes: notes.trim() || null,
    date: date.toISOString(),
  };
  if (professionalId) basePayload.professional = Number(professionalId);
  if (localId) basePayload.local_atendimento = Number(localId);
  if (convenioId) basePayload.convenio = Number(convenioId);
  if (selectedProcedures.length === 1) {
    basePayload.procedure = selectedProcedures[0];
  } else if (selectedProcedures.length > 1) {
    basePayload.procedures_ids = selectedProcedures;
    basePayload.procedure = selectedProcedures[0];
  }
  if (retornoProcedureId) {
    basePayload.retorno_procedure = Number(retornoProcedureId);
  }
  return basePayload;
}

export function computeCriarAgendamentoPricing(
  localAtendimentoId: number | "",
  locaisAtendimento: LocalAtendimentoItem[],
  retornoInfo: RetornoVerificacaoResult | null,
  resumoValor: number,
) {
  const localSel = localAtendimentoId
    ? locaisAtendimento.find((l) => l.id === localAtendimentoId)
    : undefined;
  const taxaConsultaBase = localSel ? Number(localSel.valor_consulta) || 0 : 0;
  const taxaConsulta = retornoInfo?.elegivel ? 0 : taxaConsultaBase;
  const totalEstimado = taxaConsulta + resumoValor;
  const regrasRetornoProc = retornoInfo?.regras_procedimento ?? [];
  const retornoProcAtivo = retornoInfo?.config?.retorno_procedimento_ativo ?? false;
  return { taxaConsultaBase, totalEstimado, regrasRetornoProc, retornoProcAtivo };
}

export function getCriarAgendamentoModalLabels(isConsulta: boolean, createLoading: boolean) {
  return {
    modalTitle: isConsulta ? "Nova consulta" : "Novo agendamento",
    modalSubtitle: isConsulta ? "Abrir consulta na clínica" : "Agendar atendimento na clínica",
    submitLabel: isConsulta
      ? createLoading
        ? "Abrindo..."
        : "Abrir consulta"
      : createLoading
        ? "Agendando..."
        : "Agendar",
  };
}
