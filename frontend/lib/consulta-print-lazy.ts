/** Carrega consulta-print sob demanda (abas lazy / PDF). */
import type { ConsultaPrintSecao } from "./consulta-print";

export type { ConsultaPrintMeta, ConsultaPrintSecao } from "./consulta-print";

export async function imprimirConsultaPdfLazy(consultaId: number, secao: ConsultaPrintSecao) {
  const { imprimirConsultaPdf } = await import("./consulta-print");
  return imprimirConsultaPdf(consultaId, secao);
}

export async function imprimirDocumentoPdfLazy(doc: { id: number; pdf_url?: string | null }) {
  const { imprimirDocumentoPdf } = await import("./consulta-print");
  return imprimirDocumentoPdf(doc);
}
