declare global {
  interface Window {
    MdHub?: {
      module?: { show: (module: string) => void | Promise<unknown>; hide?: (module: string) => void | Promise<unknown> };
      event?: { add: (event: string, handler: (data: unknown) => void) => void };
      command?: {
        send?: (module: string, command: string, payload?: Record<string, unknown>) => unknown;
      };
    };
    MdSinapsePrescricao?: {
      event?: { add: (event: string, handler: (module: Record<string, unknown>) => void) => void };
      setToken?: (token: string) => void;
    };
    [MEMED_READY_FLAG]?: boolean;
    __memedListenerRegistrado?: boolean;
    __memedPrescImpressaRegistrado?: boolean;
    __memedV4ReadyListener?: boolean;
    __memedV4IframeReady?: boolean;
  }
}

import {
  MEMED_COMMAND_TIMEOUT_MS,
  MEMED_CONTAINER_ID,
  MEMED_MODULO_PRESCRICAO,
  MEMED_READY_FLAG,
  MEMED_SCRIPT_ID,
  MEMED_TIMEOUT_MS,
  MEMED_V4_READY_TIMEOUT_MS,
} from "./memed-constants";
import {
  aguardarMensagemMemedReady,
  enviarComandoMemed,
  forcarFecharOverlayMemed,
  isMemedMessageReady,
  isMemedV4Boot,
} from "@/lib/memed-sdk";

let prescricaoImpressaHandler: ((data: unknown) => void) | null = null;

export function setPrescricaoImpressaHandler(handler: ((data: unknown) => void) | null): void {
  prescricaoImpressaHandler = handler;
}

export function moduloMemedPronto(): boolean {
  if (typeof window === "undefined") return false;
  return window[MEMED_READY_FLAG] === true || window.__memedV4IframeReady === true || isMemedV4Boot(window);
}

export function registrarListenerV4Ready(): void {
  if (typeof window === "undefined" || window.__memedV4ReadyListener) return;
  window.__memedV4ReadyListener = true;
  window.addEventListener("message", (event: MessageEvent) => {
    if (isMemedMessageReady(event.data)) {
      window.__memedV4IframeReady = true;
    }
  });
}

export function registrarListenerPrescricaoMemed(): void {
  if (typeof window === "undefined") return;
  registrarListenerV4Ready();
  const sinapse = window.MdSinapsePrescricao;
  if (!sinapse?.event?.add || window.__memedListenerRegistrado) return;
  window.__memedListenerRegistrado = true;
  sinapse.event.add("core:moduleInit", (module) => {
    if (module?.name !== MEMED_MODULO_PRESCRICAO) return;
    window[MEMED_READY_FLAG] = true;
    const mdhub = window.MdHub;
    if (mdhub?.event?.add && !window.__memedPrescImpressaRegistrado) {
      window.__memedPrescImpressaRegistrado = true;
      mdhub.event.add("prescricaoImpressa", (data: unknown) => {
        try {
          prescricaoImpressaHandler?.(data);
        } catch {
          // Não deixa erro de callback quebrar a Memed.
        }
      });
    }
  });
}

export function carregarScriptMemed(scriptUrl: string, token: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.getElementById(MEMED_SCRIPT_ID) as HTMLScriptElement | null;
    if (existing) {
      existing.setAttribute("data-token", token);
      existing.setAttribute("data-container", MEMED_CONTAINER_ID);
      window.MdSinapsePrescricao?.setToken?.(token);
      registrarListenerPrescricaoMemed();
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.id = MEMED_SCRIPT_ID;
    script.type = "text/javascript";
    script.src = scriptUrl;
    script.setAttribute("data-token", token);
    script.setAttribute("data-container", MEMED_CONTAINER_ID);
    script.async = true;
    script.onload = () => {
      registrarListenerPrescricaoMemed();
      resolve();
    };
    script.onerror = () => reject(new Error("Falha ao carregar o script da Memed."));
    document.body.appendChild(script);
  });
}

export function aguardarModuloMemed(): Promise<void> {
  return new Promise((resolve, reject) => {
    registrarListenerPrescricaoMemed();
    const inicio = Date.now();
    const verificar = () => {
      if (moduloMemedPronto()) {
        resolve();
        return;
      }
      if (Date.now() - inicio > MEMED_TIMEOUT_MS) {
        reject(new Error("Tempo esgotado ao iniciar a Memed. Verifique a conexão e tente novamente."));
        return;
      }
      registrarListenerPrescricaoMemed();
      setTimeout(verificar, 150);
    };
    verificar();
  });
}

export async function aguardarWidgetMemedOperacional(): Promise<void> {
  if (!isMemedV4Boot(window) || window.__memedV4IframeReady) return;
  registrarListenerV4Ready();
  await aguardarMensagemMemedReady(window, MEMED_V4_READY_TIMEOUT_MS);
}

export function preloadMemedScript(url: string): void {
  if (document.querySelector(`link[href="${url}"]`)) return;
  const link = document.createElement("link");
  link.rel = "preload";
  link.as = "script";
  link.href = url;
  document.head.appendChild(link);
}

export function fecharModuloPrescricaoMemed(): void {
  try {
    void window.MdHub?.module?.hide?.(MEMED_MODULO_PRESCRICAO);
  } catch {
    // silencioso
  }
  forcarFecharOverlayMemed(window);
}

export function logoutMemedSdk(): void {
  try {
    void window.MdHub?.command?.send?.("plataforma.sdk", "logout");
  } catch {
    // silencioso
  }
}

export function abrirModuloPrescricaoMemed(): void {
  void window.MdHub?.module?.show?.(MEMED_MODULO_PRESCRICAO);
}

export async function enviarComandoPrescricaoMemed(
  command: string,
  payload?: Record<string, unknown>,
): Promise<void> {
  await enviarComandoMemed(window, MEMED_MODULO_PRESCRICAO, command, payload, MEMED_COMMAND_TIMEOUT_MS);
}
