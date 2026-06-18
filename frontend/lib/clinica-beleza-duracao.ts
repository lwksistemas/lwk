/**
 * Duração de agendamento: tempo do profissional (ou local legado) vs soma dos procedimentos.
 */

export function tempoConsultaBaseMinutos(
  professional?: { tempo_consulta_minutos?: number | null } | null,
  local?: { tempo_consulta_minutos?: number | null } | null,
): number {
  const profTempo = professional?.tempo_consulta_minutos;
  if (profTempo != null && profTempo > 0) return profTempo;
  const localTempo = local?.tempo_consulta_minutos;
  if (localTempo != null && localTempo > 0) return localTempo;
  return 30;
}

export function calcularDuracaoAgendamento(
  duracaoProcedimentos: number,
  professional?: { tempo_consulta_minutos?: number | null } | null,
  local?: { tempo_consulta_minutos?: number | null } | null,
): number {
  const base = tempoConsultaBaseMinutos(professional, local);
  if (duracaoProcedimentos > 0) {
    return Math.max(duracaoProcedimentos, base);
  }
  return base;
}
