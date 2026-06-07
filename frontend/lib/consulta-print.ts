import { logger } from "@/lib/logger";

export interface ConsultaPrintMeta {
  patientName: string;
  professionalName: string;
  procedureName: string;
  consultaId: number;
  dataConsulta?: string;
}

export type ConsultaPrintSecao = "atendimento" | "produtos" | "anamnese" | "evolucao" | "evolucoes";

async function extrairErroApi(response: Response): Promise<string> {
  const fallback = `Erro ao gerar PDF (${response.status})`;
  try {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const data = (await response.json()) as { error?: string; detail?: string };
      return data.error || data.detail || fallback;
    }
    const text = await response.text();
    if (text.trim()) return text.slice(0, 200);
  } catch {
    // ignore
  }
  return fallback;
}

async function abrirPdfBlob(response: Response): Promise<void> {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("pdf") && !contentType.includes("octet-stream")) {
    const msg = await extrairErroApi(response);
    throw new Error(msg);
  }
  const blob = await response.blob();
  if (blob.size < 100) {
    throw new Error("PDF vazio ou inválido.");
  }
  const url = window.URL.createObjectURL(blob);
  const opened = window.open(url, "_blank");
  if (!opened) {
    window.URL.revokeObjectURL(url);
    throw new Error("Permita pop-ups para abrir o PDF.");
  }
  setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
}

/** Gera PDF da seção da consulta (logo ou papel timbrado) e abre em nova aba. */
export async function imprimirConsultaPdf(
  consultaId: number,
  secao: ConsultaPrintSecao,
): Promise<void> {
  const secaoParam = secao === "evolucoes" ? "evolucao" : secao;
  const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
  const response = await clinicaBelezaFetch(`/consultas/${consultaId}/pdf/?secao=${secaoParam}`);
  if (!response.ok) {
    const msg = await extrairErroApi(response);
    logger.warn("Erro ao gerar PDF da consulta:", response.status, msg);
    throw new Error(msg);
  }
  await abrirPdfBlob(response);
}

/** Gera PDF do documento clínico e abre em nova aba para impressão. */
export async function imprimirDocumentoPdf(doc: {
  id: number;
  pdf_url?: string | null;
}): Promise<void> {
  if (doc.pdf_url) {
    window.open(doc.pdf_url, "_blank");
    return;
  }

  const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
  const response = await clinicaBelezaFetch(`/documentos/${doc.id}/pdf/`);
  if (!response.ok) {
    const msg = await extrairErroApi(response);
    logger.warn("Erro ao gerar PDF do documento:", response.status, msg);
    throw new Error(msg);
  }
  await abrirPdfBlob(response);
}
