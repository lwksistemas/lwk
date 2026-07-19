/** Carrega consulta-print sob demanda (abas lazy / PDF). */
import type { ConsultaPdfModo, ConsultaPrintSecao } from "./consulta-print";

export type { ConsultaPrintMeta, ConsultaPrintSecao, ConsultaPdfModo } from "./consulta-print";

export async function imprimirConsultaPdfLazy(
  consultaId: number,
  secao: ConsultaPrintSecao,
  modo: ConsultaPdfModo = "visualizar",
) {
  const { imprimirConsultaPdf } = await import("./consulta-print");
  return imprimirConsultaPdf(consultaId, secao, modo);
}

export async function imprimirDocumentoPdfLazy(
  doc: { id: number; pdf_url?: string | null },
  modo: ConsultaPdfModo = "visualizar",
) {
  const { imprimirDocumentoPdf } = await import("./consulta-print");
  return imprimirDocumentoPdf(doc, modo);
}
