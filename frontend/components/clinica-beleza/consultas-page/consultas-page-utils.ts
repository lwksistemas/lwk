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

export type ConsultasListaVista = "finalizadas" | "iniciar";
export type ConsultasPeriodo = "mes_atual" | "mes_passado" | "periodo";

function isoDataLocal(d: Date): string {
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mes}-${dia}`;
}

/** Intervalo do filtro da lista. Por período usa as datas informadas. */
export function intervaloPeriodoConsultas(
  periodo: ConsultasPeriodo,
  custom: { inicio: string; fim: string } = { inicio: "", fim: "" },
  hoje: Date = new Date(),
): { data_inicio: string; data_fim: string } {
  if (periodo === "periodo") {
    return { data_inicio: custom.inicio, data_fim: custom.fim };
  }
  const ano = hoje.getFullYear();
  const mes = hoje.getMonth();
  if (periodo === "mes_passado") {
    return {
      data_inicio: isoDataLocal(new Date(ano, mes - 1, 1)),
      data_fim: isoDataLocal(new Date(ano, mes, 0)),
    };
  }
  return {
    data_inicio: isoDataLocal(new Date(ano, mes, 1)),
    data_fim: isoDataLocal(new Date(ano, mes + 1, 0)),
  };
}

/** Query da lista. Abre em Para iniciar; Finalizadas vão da mais recente para a mais antiga. */
export function buildConsultasListQueryParams(opts: {
  patientId?: number | null;
  professionalId?: number | null;
  vista?: ConsultasListaVista;
  dataInicio?: string | null;
  dataFim?: string | null;
}): Record<string, string | number> {
  const vista = opts.vista ?? "iniciar";
  const params: Record<string, string | number> = {};
  if (opts.patientId) {
    params.patient = opts.patientId;
  }
  if (vista === "finalizadas") {
    params.status = "COMPLETED";
  } else if (!opts.patientId) {
    params.fila = "iniciar";
  }
  if (opts.professionalId) {
    params.professional = opts.professionalId;
  }
  if (opts.dataInicio) params.data_inicio = opts.dataInicio;
  if (opts.dataFim) params.data_fim = opts.dataFim;
  return params;
}
