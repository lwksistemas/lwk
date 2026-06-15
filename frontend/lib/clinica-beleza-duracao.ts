/**
 * Duração de agendamento: tempo do local de atendimento vs soma dos procedimentos.
 */

export function tempoConsultaBaseMinutos(
  local?: { tempo_consulta_minutos?: number | null } | null,
): number {
  const localTempo = local?.tempo_consulta_minutos;
  if (localTempo != null && localTempo > 0) return localTempo;
  return 30;
}

export function calcularDuracaoAgendamento(
  duracaoProcedimentos: number,
  local?: { tempo_consulta_minutos?: number | null } | null,
): number {
  const base = tempoConsultaBaseMinutos(local);
  if (duracaoProcedimentos > 0) {
    return Math.max(duracaoProcedimentos, base);
  }
  return base;
}
