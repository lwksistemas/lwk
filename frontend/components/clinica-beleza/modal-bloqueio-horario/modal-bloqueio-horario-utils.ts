export const TIPOS_BLOQUEIO = [
  { value: "Férias do profissional", label: "🏖 Férias do profissional" },
  { value: "Manutenção", label: "🛠 Manutenção" },
  { value: "Evento interno", label: "📅 Evento interno" },
  { value: "", label: "✏️ Outro (digite abaixo)" },
] as const;

/** Modo do intervalo no modal Bloquear Horário. */
export type ModoBloqueioIntervalo = "dias" | "horario";

export const MODOS_BLOQUEIO_INTERVALO = [
  { value: "dias" as const, label: "Dia(s) inteiro(s)" },
  { value: "horario" as const, label: "Horário no dia" },
];

/** Tipos de motivo que sugerem bloqueio de dia(s) inteiro(s). */
export const TIPOS_SUGEREM_DIAS = ["Férias do profissional"] as const;

export interface BloqueioProfessional {
  id: number;
  name?: string;
  nome?: string;
  specialty?: string;
}

export function profissionalBloqueioLabel(p: BloqueioProfessional): string {
  return p.nome ?? p.name ?? `Profissional #${p.id}`;
}

export function resolveMotivoBloqueio(tipoSelecionado: string, motivoOutro: string): string {
  return tipoSelecionado || motivoOutro.trim() || "Bloqueio";
}

export function modoSugeridoParaTipo(tipoSelecionado: string): ModoBloqueioIntervalo {
  return (TIPOS_SUGEREM_DIAS as readonly string[]).includes(tipoSelecionado) ? "dias" : "horario";
}

export function validateBloqueioForm(params: {
  modo: ModoBloqueioIntervalo;
  motivoFinal: string;
  /** YYYY-MM-DD — modo dias */
  dataInicioDia?: string;
  dataFimDia?: string;
  /** YYYY-MM-DD — modo horario */
  dataHorario?: string;
  horaInicio?: string;
  horaFim?: string;
}): string | null {
  const { modo, motivoFinal } = params;
  if (!motivoFinal.trim()) return "Informe o motivo (tipo ou outro).";

  if (modo === "dias") {
    const { dataInicioDia, dataFimDia } = params;
    if (!dataInicioDia || !dataFimDia) return "Preencha a data de início e a data de fim.";
    if (dataFimDia < dataInicioDia) return "A data de fim deve ser igual ou depois da data de início.";
    return null;
  }

  const { dataHorario, horaInicio, horaFim } = params;
  if (!dataHorario) return "Preencha a data do bloqueio.";
  if (!horaInicio || !horaFim) return "Preencha o horário de início e fim.";
  if (horaFim <= horaInicio) return "O horário de fim deve ser depois do início.";
  return null;
}

function localDateStartIso(dateYmd: string): string {
  return new Date(`${dateYmd}T00:00:00`).toISOString();
}

function localDateEndIso(dateYmd: string): string {
  return new Date(`${dateYmd}T23:59:59`).toISOString();
}

export function buildBloqueioRequestBody(params: {
  modo: ModoBloqueioIntervalo;
  motivo: string;
  observacoes: string;
  professionalId: string;
  dataInicioDia?: string;
  dataFimDia?: string;
  dataHorario?: string;
  horaInicio?: string;
  horaFim?: string;
}): Record<string, unknown> {
  const body: Record<string, unknown> = {
    motivo: params.motivo.trim(),
  };
  if (params.observacoes.trim()) body.observacoes = params.observacoes.trim();
  if (params.professionalId) body.professional = parseInt(params.professionalId, 10);

  if (params.modo === "dias") {
    const ini = params.dataInicioDia!;
    const fim = params.dataFimDia!;
    body.data_inicio = localDateStartIso(ini);
    body.data_fim = localDateEndIso(fim);
    body.dia_inteiro = true;
    return body;
  }

  const data = params.dataHorario!;
  const inicioDate = new Date(`${data}T${params.horaInicio}:00`);
  const fimDate = new Date(`${data}T${params.horaFim}:00`);
  body.data_inicio = inicioDate.toISOString();
  body.data_fim = fimDate.toISOString();
  return body;
}

export function extractBloqueioApiError(data: Record<string, unknown>, status: number): string {
  const msg =
    data.error ||
    data.detail ||
    data.motivo ||
    (Array.isArray(data.data_inicio) ? data.data_inicio[0] : null) ||
    (Array.isArray(data.data_fim) ? data.data_fim[0] : null) ||
    `Erro ${status}`;
  return typeof msg === "string" ? msg : "Erro ao criar bloqueio.";
}

export { formatDateInputValue as formatDateInput } from "../criar-agendamento/criar-agendamento-utils";

export function formatTimeInput(d: Date): string {
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${h}:${min}`;
}
