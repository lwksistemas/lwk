/**
 * Helpers da Sinapse Memed 3.25+ (widget V4).
 * O SDK passou a devolver Promise em command.send; sem timeout o clique trava a consulta.
 */

export const MEMED_V4_BOOT_KEY = "__memedSinapseV4Boot";
export const MEMED_V4_OVERLAY_ID = "memed-auto-generated";
export const MEMED_V4_SCRIPT_PROD = "https://v4-embedded.memed.com.br/sinapse/sinapse-v4.min.js";
export const MEMED_V4_APP_URL_PROD = "https://v4-embedded.memed.com.br/";

/** Usa o script oficial do ambiente (produção ou homologação). Não forçar o V4:
 * o Unleash da Memed decide o widget; o gateway V4 rejeita token se o parceiro
 * ainda não estiver no rollout.
 */
export function urlScriptWidgetMemed(scriptUrl: string): string {
  return scriptUrl;
}

export function appUrlWidgetMemed(_scriptUrl: string): string | null {
  return null;
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

/**
 * Nunca chamar setToken depois do script com data-token: no legado isso
 * dispara startModules e recarrega o iframe (401). O V4 já lê o data-token.
 */
export function podeReforcarTokenMemed(_win: Window | undefined): boolean {
  return false;
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

export function aguardarMensagemMemedReady(win: Window, timeoutMs: number): Promise<boolean> {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (ok: boolean) => {
      if (settled) return;
      settled = true;
      win.removeEventListener("message", onMessage);
      clearTimeout(timer);
      resolve(ok);
    };
    const onMessage = (event: MessageEvent) => {
      if (isMemedMessageReady(event.data)) finish(true);
    };
    const timer = win.setTimeout(() => finish(false), timeoutMs);
    win.addEventListener("message", onMessage);
  });
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

export function ehIframeMemed(el: Element): boolean {
  if (el.tagName !== "IFRAME") return false;
  const src = el.getAttribute("src") || "";
  const title = el.getAttribute("title") || "";
  return title === "Memed Prescrição" || src.includes("v4-embedded") || src.includes("memed.com.br");
}

export function localizarIframeMemed(doc: Document): HTMLIFrameElement | null {
  const found = Array.from(doc.querySelectorAll("iframe")).find(ehIframeMemed);
  return found ? (found as HTMLIFrameElement) : null;
}

function desocultarSeNosEscondemos(el: HTMLElement): void {
  if (el.style.display === "none") el.style.display = "";
  if (el.style.visibility === "hidden") el.style.visibility = "";
  if (el.style.pointerEvents === "none") el.style.pointerEvents = "";
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
    desocultarSeNosEscondemos(iframe);
    if (overlay) {
      if (host && host.contains(iframe) && !overlay.contains(iframe) && !overlay.contains(host)) {
        overlay.style.display = "none";
        overlay.style.pointerEvents = "none";
      } else {
        desocultarSeNosEscondemos(overlay);
      }
    }
    return true;
  }

  if (overlay) {
    desocultarSeNosEscondemos(overlay);
    return overlay.childElementCount > 0;
  }
  return false;
}

/** @deprecated Use garantirEditorMemedVisivel — não move o iframe. */
export function moverIframeMemedParaHost(doc: Document, hostId: string): boolean {
  return garantirEditorMemedVisivel(doc, hostId);
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
