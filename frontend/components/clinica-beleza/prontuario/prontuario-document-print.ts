import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { ProntuarioDocItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";

export async function printMemedProntuarioDocument(doc: ProntuarioDocItem): Promise<void> {
  const { abrirPdfPrescricaoMemed } = await import("@/lib/memed-prescricao-pdf");
  await abrirPdfPrescricaoMemed({ id: doc.id, pdf_url: doc.pdf_url });
}

export async function printClinicoProntuarioDocument(doc: ProntuarioDocItem): Promise<void> {
  const response = await clinicaBelezaFetch(`/documentos/${doc.id}/pdf/`);
  if (!response.ok) {
    logger.warn("Erro ao gerar PDF do documento:", response.status);
    return;
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  window.open(url, "_blank");
  setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
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
