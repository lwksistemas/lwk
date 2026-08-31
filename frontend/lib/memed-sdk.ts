/**
 * Helpers da Sinapse Memed 3.25+ (widget V4).
 * O SDK passou a devolver Promise em command.send; sem timeout o clique trava a consulta.
 */

export const MEMED_V4_BOOT_KEY = "__memedSinapseV4Boot";
export const MEMED_V4_OVERLAY_ID = "memed-auto-generated";
export const MEMED_V4_SCRIPT_PROD = "https://v4-embedded.memed.com.br/sinapse/sinapse-v4.min.js";

/** V4 embedded é o que abre o editor. O hub clássico injeta HTML no React (#418)
 * e some o modal.
 */
export function urlScriptWidgetMemed(scriptUrl: string): string {
  if (!scriptUrl || scriptUrl.includes("integrations.")) return scriptUrl;
  return MEMED_V4_SCRIPT_PROD;
}

type MemedHubWindow = Window & {
  MdHub?: {
    command?: {
      send?: (module: string, command: string, payload?: Record<string, unknown>) => unknown;
    };
  };
  [MEMED_V4_BOOT_KEY]?: unknown;
};

export function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`${label} (${ms / 1000}s).`));
    }, ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (err) => {
        clearTimeout(timer);
        reject(err);
      },
    );
  });
}

export function isMemedV4Boot(win: Window | undefined): boolean {
  return Boolean(win && (win as MemedHubWindow)[MEMED_V4_BOOT_KEY]);
}

export function scriptMemedPrecisaReiniciar(
  tokenNoScript: string | null | undefined,
  tokenNovo: string,
  srcAtual?: string | null,
  srcAlvo?: string,
): boolean {
  if (tokenNoScript && tokenNovo && tokenNoScript !== tokenNovo) return true;
  if (srcAtual && srcAlvo) {
    const atual = srcAtual.split("?")[0];
    const alvo = srcAlvo.split("?")[0];
    if (atual && alvo && atual !== alvo) return true;
  }
  return false;
}

export function isMemedMessageReady(data: unknown): boolean {
  return Boolean(data && typeof data === "object" && (data as { type?: string }).type === "MEMED_READY");
}

export async function enviarComandoMemed(
  win: Window,
  moduleName: string,
  command: string,
  payload: Record<string, unknown> | undefined,
  timeoutMs: number,
): Promise<void> {
  const send = (win as MemedHubWindow).MdHub?.command?.send;
  if (!send) {
    throw new Error("Memed não disponível.");
  }
  const result = send(moduleName, command, payload);
  await withTimeout(Promise.resolve(result), timeoutMs, `Memed: tempo esgotado no comando ${command}`);
}

function ehIframeMemed(el: Element): boolean {
  if (el.tagName !== "IFRAME") return false;
  const src = el.getAttribute("src") || "";
  const title = el.getAttribute("title") || "";
  return title === "Memed Prescrição" || src.includes("v4-embedded") || src.includes("memed.com.br");
}

function localizarIframeMemed(doc: Document): HTMLIFrameElement | null {
  const found = Array.from(doc.querySelectorAll("iframe")).find(ehIframeMemed);
  return found ? (found as HTMLIFrameElement) : null;
}

function aplicarEstiloIframeMemed(iframe: HTMLIFrameElement): void {
  iframe.style.display = "block";
  iframe.style.width = "100%";
  iframe.style.height = "100%";
  iframe.style.minHeight = "700px";
  iframe.style.border = "none";
  iframe.style.visibility = "visible";
  iframe.style.pointerEvents = "auto";
}

function revelarOverlayMemed(overlay: HTMLElement): void {
  overlay.style.display = "block";
  overlay.style.visibility = "visible";
  overlay.style.pointerEvents = "auto";
  overlay.style.position = "fixed";
  overlay.style.inset = "0";
  overlay.style.top = "4.25rem";
  overlay.style.width = "100vw";
  overlay.style.height = "100vh";
  overlay.style.zIndex = "2147483646";
}

/**
 * Deixa o editor visível sem mover o iframe de lugar.
 * appendChild recarrega o iframe (perde o token) e a Memed responde 401.
 */
export function garantirEditorMemedVisivel(doc: Document, hostId: string): boolean {
  const host = doc.getElementById(hostId);
  const overlay = doc.getElementById(MEMED_V4_OVERLAY_ID) as HTMLElement | null;
  const iframeNoHost = host
    ? Array.from(host.querySelectorAll("iframe")).find(ehIframeMemed)
    : undefined;
  const iframe = (iframeNoHost as HTMLIFrameElement | undefined) || localizarIframeMemed(doc);

  if (iframe) {
    aplicarEstiloIframeMemed(iframe);
    if (overlay) {
      if (host && host.contains(iframe) && !overlay.contains(iframe) && !overlay.contains(host)) {
        overlay.style.display = "none";
        overlay.style.pointerEvents = "none";
      } else {
        revelarOverlayMemed(overlay);
      }
    }
    return true;
  }

  if (overlay) {
    revelarOverlayMemed(overlay);
    return overlay.childElementCount > 0;
  }
  return false;
}

export function forcarFecharOverlayMemed(win: Window, hostId?: string): void {
  const host = hostId ? win.document.getElementById(hostId) : null;
  const overlay = win.document.getElementById(MEMED_V4_OVERLAY_ID);
  if (overlay instanceof HTMLElement && (!host || !overlay.contains(host))) {
    overlay.style.display = "none";
    overlay.style.visibility = "hidden";
    overlay.style.pointerEvents = "none";
  }
  win.document.body.style.overflow = "";
}
