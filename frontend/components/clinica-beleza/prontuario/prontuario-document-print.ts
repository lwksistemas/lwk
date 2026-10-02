import type { ProntuarioDocItem } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";
import { imprimirDocumentoPdf } from "@/lib/consulta-print";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { downloadBlobFile } from "@/lib/download-blob";

export async function printMemedProntuarioDocument(
  doc: ProntuarioDocItem,
  janela?: Window | null,
): Promise<void> {
  const { abrirPdfPrescricaoMemed } = await import("@/lib/memed-prescricao-pdf");
  await abrirPdfPrescricaoMemed({ id: doc.id, pdf_url: doc.pdf_url }, "visualizar", janela);
}

export async function printClinicoProntuarioDocument(doc: ProntuarioDocItem): Promise<void> {
  await imprimirDocumentoPdf(doc);
}

/**
 * @param janela aba pré-aberta no clique do usuário (evita bloqueio de pop-up
 * quando o PDF precisa ser buscado/gerado na API antes de abrir).
 */
export async function printProntuarioDocument(
  doc: ProntuarioDocItem,
  janela?: Window | null,
): Promise<void> {
  if (doc.source === "memed") {
    await printMemedProntuarioDocument(doc, janela);
    return;
  }
  if (doc.source === "documento_clinico") {
    await printClinicoProntuarioDocument(doc);
  }
}

function nomeArquivoProntuario(nomeCliente?: string, secao?: string): string {
  const slug = (nomeCliente || "cliente")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .slice(0, 60)
    .toUpperCase() || "CLIENTE";
  return secao ? `Prontuario_${secao}_${slug}.pdf` : `Prontuario_${slug}.pdf`;
}

function nomeDoHeader(header: string | null, fallback: string): string {
  if (!header) return fallback;
  const star = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(header);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^"(.*)"$/, "$1"));
    } catch {
      /* fallback */
    }
  }
  const quoted = /filename="([^"]+)"/i.exec(header);
  return quoted?.[1] || fallback;
}

/** PDF autenticado do prontuário (seção ou completo), baixado com o nome da cliente. */
export async function imprimirProntuarioPdf(
  patientId: number,
  secao?: string,
  nomeCliente?: string,
): Promise<void> {
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
  const blob = await response.blob();
  if (blob.size < 100) {
    throw new Error("PDF vazio ou inválido.");
  }
  const nome = nomeDoHeader(
    response.headers.get("Content-Disposition"),
    nomeArquivoProntuario(nomeCliente, secao),
  );
  downloadBlobFile(blob, nome);
}
