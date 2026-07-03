export const TIPOS_BLOQUEIO = [
  { value: "Férias do profissional", label: "🏖 Férias do profissional" },
  { value: "Manutenção", label: "🛠 Manutenção" },
  { value: "Evento interno", label: "📅 Evento interno" },
  { value: "", label: "✏️ Outro (digite abaixo)" },
] as const;

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

export function validateBloqueioForm(
  dataInicio: string,
  dataFim: string,
  motivoFinal: string,
): string | null {
  if (!dataInicio || !dataFim) return "Preencha data/hora de início e fim.";
  if (new Date(dataFim) <= new Date(dataInicio)) return "O fim deve ser depois do início.";
  if (!motivoFinal.trim()) return "Informe o motivo (tipo ou outro).";
  return null;
}

export function buildBloqueioRequestBody(params: {
  dataInicio: string;
  dataFim: string;
  motivo: string;
  observacoes: string;
  professionalId: string;
}): Record<string, unknown> {
  const inicioDate = params.dataInicio.includes("T")
    ? new Date(params.dataInicio)
    : new Date(`${params.dataInicio}T12:00:00`);
  const fimDate = params.dataFim.includes("T")
    ? new Date(params.dataFim)
    : new Date(`${params.dataFim}T14:00:00`);

  const body: Record<string, unknown> = {
    data_inicio: inicioDate.toISOString(),
    data_fim: fimDate.toISOString(),
    motivo: params.motivo.trim(),
  };
  if (params.observacoes.trim()) body.observacoes = params.observacoes.trim();
  if (params.professionalId) body.professional = parseInt(params.professionalId, 10);
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
