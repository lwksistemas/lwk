import { logger } from "@/lib/logger";

export interface ConsultaPrintMeta {
  patientName: string;
  professionalName: string;
  procedureName: string;
  consultaId: number;
  dataConsulta?: string;
}

export type ConsultaPrintSecao = "atendimento" | "produtos" | "anamnese" | "evolucao" | "evolucoes";

/** visualizar = abrir PDF na aba; imprimir = mesma coisa (viewer nativo do Chrome imprime certo).
 *  O wrapper com iframe+print() gera preview em branco no Chrome — não usar. */
export type ConsultaPdfModo = "visualizar" | "imprimir";

/**
 * @deprecated Preferir abrir o PDF nativo (location.href). Mantido só para testes legados.
 * iframe + print() no Chrome deixa o preview em branco.
 */
export function escreverPaginaImpressaoPdf(win: Window, url: string): void {
  win.location.href = url;
}

/** Imprime HTML de cupom via iframe oculto na página atual (evita popup 320px com print quebrado). */
export function imprimirHtmlDocumento(html: string): void {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("aria-hidden", "true");
  iframe.setAttribute("title", "Impressão");
  Object.assign(iframe.style, {
    position: "fixed",
    right: "0",
    bottom: "0",
    width: "0",
    height: "0",
    border: "0",
    opacity: "0",
    pointerEvents: "none",
  });
  document.body.appendChild(iframe);
  const doc = iframe.contentDocument;
  const win = iframe.contentWindow;
  if (!doc || !win) {
    iframe.remove();
    throw new Error("Não foi possível preparar a impressão.");
  }
  doc.open();
  doc.write(html);
  doc.close();

  let done = false;
  const cleanup = () => {
    if (done) return;
    done = true;
    setTimeout(() => {
      try {
        iframe.remove();
      } catch {
        /* silencioso */
      }
    }, 1500);
  };

  const go = () => {
    try {
      win.focus();
      win.print();
    } finally {
      cleanup();
    }
  };

  // load nem sempre dispara após document.write; agenda os dois caminhos
  iframe.addEventListener("load", () => setTimeout(go, 50));
  setTimeout(go, 300);
}

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

export function abrirPdfUrl(url: string, modo: ConsultaPdfModo = "visualizar"): void {
  void modo;
  const opened = window.open(url, "_blank");
  if (!opened) {
    throw new Error("Permita pop-ups para abrir o PDF.");
  }
}

/**
 * Abre uma aba em branco IMEDIATAMENTE (dentro do clique do usuário) para depois
 * receber a URL do PDF. Necessário quando a URL só fica disponível após um await
 * (ex.: buscar/gerar o PDF na API): abrir depois do await é bloqueado como pop-up.
 * Retorna null se o navegador bloqueou o pop-up já no clique.
 */
export function abrirJanelaPdf(): Window | null {
  return window.open("", "_blank");
}

/** Direciona uma aba pré-aberta (abrirJanelaPdf) para a URL do PDF já resolvida. */
export function direcionarJanelaPdf(
  win: Window | null,
  url: string,
  modo: ConsultaPdfModo = "visualizar",
): void {
  void modo;
  if (!win) {
    abrirPdfUrl(url, "visualizar");
    return;
  }
  win.location.href = url;
}

/** Fecha a aba pré-aberta quando a resolução do PDF falhou. */
export function fecharJanelaPdf(win: Window | null): void {
  try {
    win?.close();
  } catch {
    // silencioso
  }
}

function filenameFromContentDisposition(header: string | null | undefined): string | null {
  if (!header) return null;
  const star = header.match(/filename\*=(?:UTF-8''|utf-8'')([^;]+)/i);
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^"+|"+$/g, ""));
    } catch {
      return star[1].trim().replace(/^"+|"+$/g, "");
    }
  }
  const plain = header.match(/filename="([^"]+)"/i) || header.match(/filename=([^;]+)/i);
  return plain?.[1]?.trim() || null;
}

export async function abrirPdfBlobFromResponse(
  response: Response,
  modo: ConsultaPdfModo = "visualizar",
  janela?: Window | null,
): Promise<void> {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("pdf") && !contentType.includes("octet-stream")) {
    const msg = await extrairErroApi(response);
    throw new Error(msg);
  }
  const blob = await response.blob();
  if (blob.size < 100) {
    throw new Error("PDF vazio ou inválido.");
  }
  // File com nome do Content-Disposition: o Chrome usa esse nome no download (não o UUID do blob:).
  const nome = filenameFromContentDisposition(response.headers.get("content-disposition"));
  const arquivo =
    nome && nome.toLowerCase().endsWith(".pdf")
      ? new File([blob], nome, { type: "application/pdf" })
      : blob;
  const url = window.URL.createObjectURL(arquivo);
  try {
    if (janela !== undefined) {
      direcionarJanelaPdf(janela, url, modo);
    } else {
      abrirPdfUrl(url, modo);
    }
  } catch (e) {
    window.URL.revokeObjectURL(url);
    throw e;
  }
  setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
}

/** Gera PDF da seção da consulta (logo ou papel timbrado) e abre em nova aba. */
export async function imprimirConsultaPdf(
  consultaId: number,
  secao: ConsultaPrintSecao,
  modo: ConsultaPdfModo = "visualizar",
): Promise<void> {
  const secaoParam = secao === "evolucoes" ? "evolucao" : secao;
  const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
  const response = await clinicaBelezaFetch(`/consultas/${consultaId}/pdf/?secao=${secaoParam}`);
  if (!response.ok) {
    const msg = await extrairErroApi(response);
    logger.warn("Erro ao gerar PDF da consulta:", response.status, msg);
    throw new Error(msg);
  }
  await abrirPdfBlobFromResponse(response, modo);
}

/** Gera PDF do documento clínico e abre em nova aba. */
export async function imprimirDocumentoPdf(
  doc: {
    id: number;
    pdf_url?: string | null;
  },
  modo: ConsultaPdfModo = "visualizar",
): Promise<void> {
  if (doc.pdf_url) {
    abrirPdfUrl(doc.pdf_url, modo);
    return;
  }

  const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
  const response = await clinicaBelezaFetch(`/documentos/${doc.id}/pdf/`);
  if (!response.ok) {
    const msg = await extrairErroApi(response);
    logger.warn("Erro ao gerar PDF do documento:", response.status, msg);
    throw new Error(msg);
  }
  await abrirPdfBlobFromResponse(response, modo);
}
