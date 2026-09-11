import { ClinicaBelezaAPI, type PrescricaoMemedItem } from "@/lib/clinica-beleza-api";
import {
  abrirPdfUrl,
  direcionarJanelaPdf,
  fecharJanelaPdf,
  type ConsultaPdfModo,
} from "@/lib/consulta-print";

function mensagemErroApi(erro: unknown): string {
  if (erro instanceof Error) return erro.message;
  if (erro && typeof erro === "object") {
    const api = erro as { error?: string; detail?: string };
    if (api.error) return api.error;
    if (typeof api.detail === "string") return api.detail;
  }
  return "PDF da prescrição não disponível.";
}

/**
 * Abre o PDF da prescrição Memed pedindo de novo à API.
 *
 * Sempre consulta o backend: o PDF assinado da Memed pode chegar depois do
 * fallback local. A abertura ocorre após um await, então o chamador deve
 * passar uma aba já aberta no clique (`janela`).
 */
export async function abrirPdfPrescricaoMemed(
  prescricao: Pick<PrescricaoMemedItem, "id" | "pdf_url">,
  modo: ConsultaPdfModo = "visualizar",
  janela?: Window | null,
): Promise<string> {
  try {
    const res = await ClinicaBelezaAPI.memed.obterPdf(prescricao.id);
    const url = (res.pdf_url || "").trim() || (prescricao.pdf_url || "").trim();
    if (!url) {
      throw new Error("PDF da prescrição não disponível.");
    }
    if (janela !== undefined) direcionarJanelaPdf(janela, url, modo);
    else abrirPdfUrl(url, modo);
    return url;
  } catch (erro) {
    const salvo = (prescricao.pdf_url || "").trim();
    if (salvo) {
      if (janela !== undefined) direcionarJanelaPdf(janela, salvo, modo);
      else abrirPdfUrl(salvo, modo);
      return salvo;
    }
    if (janela !== undefined) fecharJanelaPdf(janela);
    throw new Error(mensagemErroApi(erro));
  }
}
