import type {
  Anamnese,
  Consulta,
  TabId,
} from "@/components/clinica-beleza/consultas/consultas-types";
import { EMPTY_ANAMNESE } from "@/components/clinica-beleza/consultas/consultas-types";

export const TABS_WITHOUT_REMOTE_LOAD: TabId[] = ["produtos", "documentos", "fotos"];

export function isTabWithoutRemoteLoad(tabId: TabId): boolean {
  return TABS_WITHOUT_REMOTE_LOAD.includes(tabId);
}

export function mergeAnamnese(anam: Partial<Anamnese> | null | undefined): Anamnese {
  return { ...EMPTY_ANAMNESE, ...anam };
}

export function normalizeConsultaList(data: unknown): Consulta[] {
  return Array.isArray(data) ? (data as Consulta[]) : [];
}

export function extractObservacoesConsulta(c: Consulta): string {
  return c.observacoes_gerais || c.protocolo_notas || "";
}

export function resolveInitialConsultaTab(status: string, historicoCount: number): TabId {
  const temHistoricoAnterior = historicoCount > 1;
  return status === "SCHEDULED" && temHistoricoAnterior ? "historico" : "atendimento";
}

export function mergeConsultaFresh(base: Consulta, fresh: Partial<Consulta> | null): Consulta {
  return fresh ? { ...base, ...fresh } : base;
}

export function temHistoricoAnterior(historico: Consulta[]): boolean {
  return historico.length > 1;
}
