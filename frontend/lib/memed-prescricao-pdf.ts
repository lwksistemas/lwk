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
 * Se a clínica já tem o arquivo, a aba abre na hora. O link da Memed dura
 * 10 minutos e não é aberto: o backend baixa o PDF e devolve o arquivo da clínica.
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

function linkTemporarioMemed(url: string): boolean {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return host === "memed.com.br" || host.endsWith(".memed.com.br");
  } catch {
    return false;
  }
}

function arquivoDaClinica(url: string): boolean {
  return url.includes("media.lwksistemas.com.br/files/") && !linkTemporarioMemed(url);
}

export async function abrirPdfPrescricaoMemed(
  prescricao: Pick<PrescricaoMemedItem, "id" | "pdf_url">,
  modo: ConsultaPdfModo = "visualizar",
  janela?: Window | null,
): Promise<string> {
  const salvo = (prescricao.pdf_url || "").trim();
  const salvoNaClinica = arquivoDaClinica(salvo);
  if (salvoNaClinica) abrir(salvo, modo, janela);
  try {
    const res = await ClinicaBelezaAPI.memed.obterPdf(prescricao.id);
    const url = arquivoDaClinica((res.pdf_url || "").trim()) ? res.pdf_url.trim() : "";
    if (url) {
      if (!salvoNaClinica || caminhoPdf(url) !== caminhoPdf(salvo)) abrir(url, modo, janela);
      return url;
    }
    if (salvoNaClinica) return salvo;
    throw new Error("PDF da prescrição não disponível.");
  } catch (erro) {
    if (salvoNaClinica) return salvo;
    if (janela !== undefined) fecharJanelaPdf(janela);
    throw new Error(mensagemErroApi(erro));
  }
}
