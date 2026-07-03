import type { TabId } from "./consultas-types";

export function temHistoricoAnterior(historico: unknown[]): boolean {
  return historico.length > 1;
}

export function deveExibirAguardandoInicio(
  consultaAtiva: boolean,
  consultaFinalizada: boolean,
  tab: TabId,
): boolean {
  return !consultaAtiva && !consultaFinalizada && tab !== "historico";
}

export function loadingConsultaLabel(loadingDetalhe: boolean): string {
  return loadingDetalhe ? "Carregando consulta..." : "Carregando aba...";
}
