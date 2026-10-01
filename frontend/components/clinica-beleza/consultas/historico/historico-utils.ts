import type { DocumentoClinicoItem } from "@/lib/clinica-beleza-api";
import type { PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { DOCUMENTO_TIPO_LABEL } from "../documentos/documentos-types";

export const TIPO_LABELS: Record<string, string> = DOCUMENTO_TIPO_LABEL;

export function parseListaDocumentos(data: unknown): DocumentoClinicoItem[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object" && Array.isArray((data as { results?: unknown }).results)) {
    return (data as { results: DocumentoClinicoItem[] }).results;
  }
  return [];
}

export function labelPrescricaoMemed(p: PrescricaoMemedItem): string {
  const ehExame = p.itens?.some((it) => it.tipo === "exame");
  return ehExame ? "Exames (Memed)" : "Receituário (Memed)";
}

export function agruparPrescricoesPorConsulta(
  prescricoes: PrescricaoMemedItem[],
): Record<number, PrescricaoMemedItem[]> {
  return prescricoes.reduce<Record<number, PrescricaoMemedItem[]>>((acc, p) => {
    if (p.consulta == null) return acc;
    if (!acc[p.consulta]) acc[p.consulta] = [];
    acc[p.consulta].push(p);
    return acc;
  }, {});
}
