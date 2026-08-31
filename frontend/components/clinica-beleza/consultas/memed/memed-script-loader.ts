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
      init?: (opts?: { token?: string }) => void;
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
} from "./memed-constants";
import {
  enviarComandoMemed,
  forcarFecharOverlayMemed,
  isMemedMessageReady,
  isMemedV4Boot,
  garantirEditorMemedVisivel,
  scriptMemedPrecisaReiniciar,
  urlScriptWidgetMemed,
  MEMED_V4_BOOT_KEY,
  MEMED_V4_OVERLAY_ID,
} from "@/lib/memed-sdk";

let prescricaoImpressaHandler: ((data: unknown) => void) | null = null;

export function setPrescricaoImpressaHandler(handler: ((data: unknown) => void) | null): void {
  prescricaoImpressaHandler = handler;
}

function moduloMemedPronto(): boolean {
  if (typeof window === "undefined") return false;
  return window[MEMED_READY_FLAG] === true || window.__memedV4IframeReady === true || isMemedV4Boot(window);
}

function registrarListenerV4Ready(): void {
  if (typeof window === "undefined" || window.__memedV4ReadyListener) return;
  window.__memedV4ReadyListener = true;
  window.addEventListener("message", (event: MessageEvent) => {
    if (isMemedMessageReady(event.data)) {
      window.__memedV4IframeReady = true;
    }
  });
}

function registrarPrescricaoImpressa(): void {
  const mdhub = window.MdHub;
  if (!mdhub?.event?.add || window.__memedPrescImpressaRegistrado) return;
  window.__memedPrescImpressaRegistrado = true;
  mdhub.event.add("prescricaoImpressa", (data: unknown) => {
    try {
      prescricaoImpressaHandler?.(data);
    } catch {
      // Não deixa erro de callback quebrar a Memed.
    }
  });
}

function registrarListenerPrescricaoMemed(): void {
  if (typeof window === "undefined") return;
  registrarListenerV4Ready();
  registrarPrescricaoImpressa();
  const sinapse = window.MdSinapsePrescricao;
  if (!sinapse?.event?.add || window.__memedListenerRegistrado) return;
  window.__memedListenerRegistrado = true;
  sinapse.event.add("core:moduleInit", (module) => {
    if (module?.name !== MEMED_MODULO_PRESCRICAO) return;
    window[MEMED_READY_FLAG] = true;
    registrarPrescricaoImpressa();
  });
}

function esperarMdHub(timeoutMs = MEMED_TIMEOUT_MS): Promise<void> {
  return new Promise((resolve, reject) => {
    const inicio = Date.now();
    const tick = () => {
      if (window.MdHub?.module?.show && window.MdHub?.command?.send) {
        resolve();
        return;
      }
      if (Date.now() - inicio > timeoutMs) {
        reject(new Error("A Memed não inicializou. Feche e tente novamente."));
        return;
      }
      setTimeout(tick, 100);
    };
    tick();
  });
}

function teardownMemedSdk(): void {
  try {
    const boot = (window as Window & { [MEMED_V4_BOOT_KEY]?: { teardown?: () => void } })[MEMED_V4_BOOT_KEY];
    boot?.teardown?.();
  } catch {
    // silencioso
  }
  document.getElementById("memed-sinapse-v4")?.remove();
  document.getElementById(MEMED_SCRIPT_ID)?.remove();
  document.getElementById(MEMED_V4_OVERLAY_ID)?.remove();
  document.getElementById("memed-sw-register")?.remove();
  document.getElementById("iframe-container")?.remove();
  window[MEMED_READY_FLAG] = false;
  window.__memedListenerRegistrado = false;
  window.__memedPrescImpressaRegistrado = false;
  window.__memedV4ReadyListener = false;
  window.__memedV4IframeReady = false;
  try {
    delete window.MdHub;
    delete window.MdSinapsePrescricao;
  } catch {
    // silencioso
  }
}

function aplicarAtributosScriptMemed(el: HTMLScriptElement, token: string): void {
  el.setAttribute("data-token", token);
  el.removeAttribute("data-container");
  el.removeAttribute("data-variant");
  el.removeAttribute("data-app-url");
}

export async function carregarScriptMemed(scriptUrl: string, token: string): Promise<void> {
  const src = urlScriptWidgetMemed(scriptUrl);
  const existing = document.getElementById(MEMED_SCRIPT_ID) as HTMLScriptElement | null;

  // Se já existe script com o mesmo token e URL, reutiliza sem reinjetar.
  if (existing) {
    const precisaReiniciar = scriptMemedPrecisaReiniciar(
      existing.getAttribute("data-token"),
      token,
      existing.src,
      src,
    );
    if (!precisaReiniciar) {
      registrarListenerPrescricaoMemed();
      await aguardarModuloMemed();
      return;
    }
    teardownMemedSdk();
  }

  // Widget V4: data-token no carregamento; o script gerencia o próprio ciclo de vida.
  await new Promise<void>((resolve, reject) => {
    const el = document.createElement("script");
    el.id = MEMED_SCRIPT_ID;
    el.type = "text/javascript";
    aplicarAtributosScriptMemed(el, token);
    el.src = src;
    el.addEventListener("load", () => {
      registrarListenerPrescricaoMemed();
      resolve();
    });
    el.addEventListener("error", () => reject(new Error("Falha ao carregar o script da Memed.")));
    document.head.appendChild(el);
  });

  await esperarMdHub();
  registrarListenerPrescricaoMemed();
}

function aguardarModuloMemed(): Promise<void> {
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

export function fecharModuloPrescricaoMemed(): void {
  try {
    void window.MdHub?.module?.hide?.(MEMED_MODULO_PRESCRICAO);
  } catch {
    // silencioso
  }
  forcarFecharOverlayMemed(window, MEMED_CONTAINER_ID);
}

export function abrirModuloPrescricaoMemed(): void {
  void window.MdHub?.module?.show?.(MEMED_MODULO_PRESCRICAO);
  garantirEditorMemedVisivel(document, MEMED_CONTAINER_ID);
}

export async function enviarComandoPrescricaoMemed(
  command: string,
  payload?: Record<string, unknown>,
): Promise<void> {
  await enviarComandoMemed(window, MEMED_MODULO_PRESCRICAO, command, payload, MEMED_COMMAND_TIMEOUT_MS);
}
