import { formatClinicaDateTime } from "@/lib/clinica-beleza-datetime";
import { formatApiErrorBody } from "@/lib/api-errors";
import type { Consulta } from "../consultas/consultas-types";

export function buildConsultasBasePath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/consultas`;
}

export function buildConsultaDetailHref(slug: string, consultaId: number): string {
  return `${buildConsultasBasePath(slug)}?id=${consultaId}`;
}

export function formatConsultaListDate(date?: string | null): string {
  return date ? formatClinicaDateTime(new Date(date)) : "—";
}

export function findConsultaInList(consultas: Consulta[], idParam: string): Consulta | undefined {
  return consultas.find((c) => String(c.id) === idParam);
}

export function extractConsultaDeepLinkError(e: unknown): string {
  return formatApiErrorBody(e) || "Consulta não encontrada ou sem permissão para visualizá-la.";
}

export function isNovaConsultaQuery(searchParams: URLSearchParams): boolean {
  return searchParams.get("novo") === "1";
}

/** Query da lista: fila da recepção, ou histórico do paciente; profissional é opcional. */
export function buildConsultasListQueryParams(opts: {
  patientId?: number | null;
  professionalId?: number | null;
}): Record<string, string | number> {
  const params: Record<string, string | number> = {};
  if (opts.patientId) {
    params.patient = opts.patientId;
  } else {
    params.fila = "iniciar";
  }
  if (opts.professionalId) {
    params.professional = opts.professionalId;
  }
  return params;
}
