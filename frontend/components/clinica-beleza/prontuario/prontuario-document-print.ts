import type { ProntuarioDocItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { abrirPdfBlobFromResponse, imprimirDocumentoPdf } from "@/lib/consulta-print";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";

export async function printMemedProntuarioDocument(doc: ProntuarioDocItem): Promise<void> {
  const { abrirPdfPrescricaoMemed } = await import("@/lib/memed-prescricao-pdf");
  await abrirPdfPrescricaoMemed({ id: doc.id, pdf_url: doc.pdf_url });
}

export async function printClinicoProntuarioDocument(doc: ProntuarioDocItem): Promise<void> {
  await imprimirDocumentoPdf(doc);
}

export async function printProntuarioDocument(doc: ProntuarioDocItem): Promise<void> {
  if (doc.source === "memed") {
    await printMemedProntuarioDocument(doc);
    return;
  }
  if (doc.source === "documento_clinico") {
    await printClinicoProntuarioDocument(doc);
  }
}

/** PDF autenticado do prontuário (seção ou completo). */
export async function imprimirProntuarioPdf(patientId: number, secao?: string): Promise<void> {
  const query = secao ? `?secao=${encodeURIComponent(secao)}` : "";
  const response = await clinicaBelezaFetch(`/patients/${patientId}/prontuario/pdf/${query}`);
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    let detail = `Erro ao gerar PDF (${response.status})`;
    if (contentType.includes("application/json")) {
      try {
        const data = (await response.json()) as { error?: string; detail?: string };
        detail = data.error || data.detail || detail;
      } catch {
        /* ignore */
      }
    }
    logger.warn("Erro ao gerar PDF do prontuário:", response.status, detail);
    throw new Error(detail);
  }
  await abrirPdfBlobFromResponse(response);
}
