/**
 * Helpers da Sinapse Memed 3.25+ (widget V4).
 * O SDK passou a devolver Promise em command.send; sem timeout o clique trava a consulta.
 */

export const MEMED_V4_BOOT_KEY = "__memedSinapseV4Boot";
export const MEMED_V4_OVERLAY_ID = "memed-auto-generated";

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

export function forcarFecharOverlayMemed(win: Window): void {
  const overlay = win.document.getElementById(MEMED_V4_OVERLAY_ID);
  if (overlay instanceof HTMLElement) {
    overlay.style.visibility = "hidden";
    overlay.style.pointerEvents = "none";
  }
  win.document.body.style.overflow = "";
}
