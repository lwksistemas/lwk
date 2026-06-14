/**
 * Duração de agendamento: tempo do profissional vs soma dos procedimentos.
 */

export function tempoConsultaBaseMinutos(
  professional?: { tempo_consulta_minutos?: number | null } | null,
  local?: { tempo_consulta_minutos?: number | null } | null,
): number {
  const prof = professional?.tempo_consulta_minutos;
  if (prof != null && prof > 0) return prof;
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
