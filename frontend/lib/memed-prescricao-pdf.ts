import { ClinicaBelezaAPI, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import { abrirPdfUrl, type ConsultaPdfModo } from "@/lib/consulta-print";

function mensagemErroApi(erro: unknown): string {
  if (erro instanceof Error) return erro.message;
  if (erro && typeof erro === "object") {
    const api = erro as { error?: string; detail?: string };
    if (api.error) return api.error;
    if (typeof api.detail === "string") return api.detail;
  }
  return "PDF da prescrição não disponível.";
}

/** Abre o PDF da prescrição Memed — busca na API se ainda não estiver salvo. */
export async function abrirPdfPrescricaoMemed(
  prescricao: Pick<PrescricaoMemedItem, "id" | "pdf_url">,
  modo: ConsultaPdfModo = "visualizar",
): Promise<string> {
  const salvo = (prescricao.pdf_url || "").trim();
  if (salvo) {
    abrirPdfUrl(salvo, modo);
    return salvo;
  }

  try {
    const res = await ClinicaBelezaAPI.memed.obterPdf(prescricao.id);
    const url = (res.pdf_url || "").trim();
    if (!url) {
      throw new Error("PDF da prescrição não disponível.");
    }
    abrirPdfUrl(url, modo);
    return url;
  } catch (erro) {
    throw new Error(mensagemErroApi(erro));
  }
}
