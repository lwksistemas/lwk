import { logger } from "@/lib/logger";

export interface ConsultaPrintMeta {
  patientName: string;
  professionalName: string;
  procedureName: string;
  consultaId: number;
  dataConsulta?: string;
}

export type ConsultaPrintSecao = "atendimento" | "produtos" | "anamnese" | "evolucao" | "evolucoes";

/** visualizar = abrir PDF na aba; imprimir = acionar o diálogo da impressora. */
export type ConsultaPdfModo = "visualizar" | "imprimir";

function escaparUrlHtml(url: string): string {
  return url.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}

/** Página HTML com o PDF embutido + window.print() — o viewer nativo ignora print(). */
export function escreverPaginaImpressaoPdf(win: Window, url: string): void {
  const src = escaparUrlHtml(url);
  win.document.open();
  win.document.write(`<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Imprimir</title>
  <style>
    html, body { margin: 0; height: 100%; background: #525659; }
    iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
  </style>
</head>
<body>
  <iframe id="pdf" title="PDF" src="${src}"></iframe>
  <script>
    (function () {
      var frame = document.getElementById("pdf");
      var printed = false;
      function go() {
        if (printed) return;
        printed = true;
        try {
          var cw = frame && frame.contentWindow;
          if (cw) { cw.focus(); cw.print(); return; }
        } catch (e) {}
        try { window.focus(); window.print(); } catch (e2) {}
      }
      if (frame) frame.addEventListener("load", function () { setTimeout(go, 400); });
      setTimeout(go, 1600);
    })();
  </script>
</body>
</html>`);
  win.document.close();
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
  if (modo === "imprimir") {
    const opened = window.open("", "_blank");
    if (!opened) {
      throw new Error("Permita pop-ups para imprimir o PDF.");
    }
    escreverPaginaImpressaoPdf(opened, url);
    return;
  }
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
  if (!win) {
    abrirPdfUrl(url, modo);
    return;
  }
  if (modo === "imprimir") {
    escreverPaginaImpressaoPdf(win, url);
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
  const url = window.URL.createObjectURL(blob);
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
