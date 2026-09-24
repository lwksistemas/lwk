import type { RetornoVerificacaoResult } from "@/lib/clinica-beleza-api";
import type { LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { resolveProcedureCategoriaSlug } from "@/lib/clinica-beleza-categories";

export type ProtocoloFormaCobranca = "POR_CONSULTA" | "TOTAL";

export interface ProtocoloAgendaResumo {
  id: number;
  nome: string;
  procedure: number;
  sessoes: number;
  tempo_estimado: number;
  intervalo_quantidade: number;
  intervalo_unidade: "dias" | "semanas" | "meses";
}

export type SelecaoProtocolo =
  | { tipo: "normal" }
  | { tipo: "agendar"; protocolo: ProtocoloAgendaResumo }
  | { tipo: "erro"; mensagem: string };

export function classificarSelecaoProtocolo(
  procedures: { id: number; categoria?: string | null; category?: string | null }[],
  selectedIds: number[],
  protocolos: ProtocoloAgendaResumo[],
): SelecaoProtocolo {
  const selecionados = selectedIds
    .map((id) => procedures.find((item) => item.id === id))
    .filter((item): item is { id: number; categoria?: string | null; category?: string | null } => Boolean(item));
  const ligados = protocolos.filter((item) => selectedIds.includes(item.procedure));
  const daCategoria = selecionados.some(
    (item) => resolveProcedureCategoriaSlug(item.categoria || item.category) === "protocolo",
  );
  if (selectedIds.length > 1 && (ligados.length > 0 || daCategoria)) {
    return { tipo: "erro", mensagem: "O protocolo é agendado sozinho." };
  }
  if (ligados.length > 1) {
    return {
      tipo: "erro",
      mensagem: "Há mais de um protocolo ativo neste procedimento. Deixe só um ativo.",
    };
  }
  if (ligados.length === 1 && selectedIds.length === 1) {
    return { tipo: "agendar", protocolo: ligados[0] };
  }
  if (daCategoria) {
    return {
      tipo: "erro",
      mensagem: "Cadastre o protocolo deste procedimento em Protocolos antes de agendar.",
    };
  }
  return { tipo: "normal" };
}

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

export interface CriarAgendamentoPayload {
  patient: number;
  nome_agenda: number;
  notes: string | null;
  date: string;
  professional: number;
  local_atendimento?: number;
  convenio?: number;
  procedure?: number;
  procedures_ids?: number[];
  retorno_procedure?: number;
  forma_cobranca?: ProtocoloFormaCobranca;
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
  formaCobranca,
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
  formaCobranca?: ProtocoloFormaCobranca;
}): CriarAgendamentoPayload {
  const basePayload: CriarAgendamentoPayload = {
    patient: Number(patientId),
    nome_agenda: Number(agendaId),
    notes: notes.trim() || null,
    date: date.toISOString(),
    professional: Number(professionalId),
  };
  if (localId) basePayload.local_atendimento = Number(localId);
  if (convenioId) basePayload.convenio = Number(convenioId);
  if (selectedProcedures.length === 1) {
    basePayload.procedure = selectedProcedures[0];
  } else if (selectedProcedures.length > 1) {
    basePayload.procedures_ids = selectedProcedures;
    basePayload.procedure = selectedProcedures[0];
  }
  if (retornoProcedureId && !formaCobranca) {
    basePayload.retorno_procedure = Number(retornoProcedureId);
  }
  if (formaCobranca) basePayload.forma_cobranca = formaCobranca;
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
    modalSubtitle: isConsulta
      ? "Abrir consulta na clínica — receba o pagamento em Consultas"
      : "Agendar atendimento na clínica",
    submitLabel: isConsulta
      ? createLoading
        ? "Abrindo..."
        : "Abrir consulta"
      : createLoading
        ? "Agendando..."
        : "Agendar",
  };
}
