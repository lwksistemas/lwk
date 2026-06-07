import { ClinicaBelezaAPI, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";

/** Abre o PDF da prescrição Memed — busca na API se ainda não estiver salvo. */
export async function abrirPdfPrescricaoMemed(
  prescricao: Pick<PrescricaoMemedItem, "id" | "pdf_url">,
): Promise<string> {
  const salvo = (prescricao.pdf_url || "").trim();
  if (salvo) {
    window.open(salvo, "_blank");
    return salvo;
  }

  const res = await ClinicaBelezaAPI.memed.obterPdf(prescricao.id);
  const url = (res.pdf_url || "").trim();
  if (!url) {
    throw new Error("PDF da prescrição não disponível.");
  }
  window.open(url, "_blank");
  return url;
}
