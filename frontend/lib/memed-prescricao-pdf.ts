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
 * Abre o PDF da prescrição Memed.
 *
 * Se a clínica já tem o arquivo, a aba abre na hora. A API só entra de novo
 * quando o PDF assinado ainda não substituiu o fallback local. O chamador
 * passa uma aba aberta no clique (`janela`) para o navegador não bloquear.
 */
function caminhoPdf(url: string): string {
  try {
    return new URL(url).pathname;
  } catch {
    return url.split("?")[0];
  }
}

function abrir(url: string, modo: ConsultaPdfModo, janela?: Window | null) {
  if (janela !== undefined) direcionarJanelaPdf(janela, url, modo);
  else abrirPdfUrl(url, modo);
}

export async function abrirPdfPrescricaoMemed(
  prescricao: Pick<PrescricaoMemedItem, "id" | "pdf_url">,
  modo: ConsultaPdfModo = "visualizar",
  janela?: Window | null,
): Promise<string> {
  const salvo = (prescricao.pdf_url || "").trim();
  const salvoNaClinica = salvo.includes("media.lwksistemas.com.br/files/");
  if (salvoNaClinica) abrir(salvo, modo, janela);
  try {
    const res = await ClinicaBelezaAPI.memed.obterPdf(prescricao.id);
    const url = (res.pdf_url || "").trim() || salvo;
    if (!url) {
      throw new Error("PDF da prescrição não disponível.");
    }
    if (!salvoNaClinica || caminhoPdf(url) !== caminhoPdf(salvo)) abrir(url, modo, janela);
    return url;
  } catch (erro) {
    if (salvo) {
      if (!salvoNaClinica) abrir(salvo, modo, janela);
      return salvo;
    }
    if (janela !== undefined) fecharJanelaPdf(janela);
    throw new Error(mensagemErroApi(erro));
  }
}
