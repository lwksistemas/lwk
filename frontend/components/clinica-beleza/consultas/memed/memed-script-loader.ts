declare global {
  interface Window {
    MdHub?: {
      module?: { show: (module: string) => void; hide?: (module: string) => void };
      event?: { add: (event: string, handler: (data: unknown) => void) => void };
      command?: { send?: (module: string, command: string, payload?: Record<string, unknown>) => void };
    };
    MdSinapsePrescricao?: {
      event?: { add: (event: string, handler: (module: Record<string, unknown>) => void) => void };
    };
    [MEMED_READY_FLAG]?: boolean;
    __memedListenerRegistrado?: boolean;
    __memedPrescImpressaRegistrado?: boolean;
  }
}

import {
  MEMED_MODULO_PRESCRICAO,
  MEMED_READY_FLAG,
  MEMED_SCRIPT_ID,
  MEMED_TIMEOUT_MS,
} from "./memed-constants";

let prescricaoImpressaHandler: ((data: unknown) => void) | null = null;

export function setPrescricaoImpressaHandler(handler: ((data: unknown) => void) | null): void {
  prescricaoImpressaHandler = handler;
}

export function moduloMemedPronto(): boolean {
  return typeof window !== "undefined" && window[MEMED_READY_FLAG] === true;
}

export function registrarListenerPrescricaoMemed(): void {
  if (typeof window === "undefined") return;
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
      registrarListenerPrescricaoMemed();
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.id = MEMED_SCRIPT_ID;
    script.type = "text/javascript";
    script.src = scriptUrl;
    script.setAttribute("data-token", token);
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
    window.MdHub?.module?.hide?.(MEMED_MODULO_PRESCRICAO);
  } catch {
    // silencioso
  }
}

export function logoutMemedSdk(): void {
  try {
    window.MdHub?.command?.send?.("plataforma.sdk", "logout");
  } catch {
    // silencioso
  }
}

export function abrirModuloPrescricaoMemed(): void {
  window.MdHub?.module?.show?.(MEMED_MODULO_PRESCRICAO);
}
