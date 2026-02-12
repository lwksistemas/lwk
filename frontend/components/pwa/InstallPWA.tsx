"use client";

import { useEffect, useState } from "react";

function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window.navigator as { standalone?: boolean }).standalone === true
  );
}

function isIOS(): boolean {
  if (typeof navigator === "undefined") return false;
  return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

export function InstallPWA() {
  const [prompt, setPrompt] = useState<{ prompt: () => Promise<void> } | null>(null);
  const [visible, setVisible] = useState(false);
  const [showIOSHint, setShowIOSHint] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (isStandalone() || dismissed) return;

    const handler = (e: Event) => {
      e.preventDefault();
      const ev = e as unknown as { prompt: () => Promise<void> };
      setPrompt(ev);
      setVisible(true);
    };
    window.addEventListener("beforeinstallprompt", handler);

    const ios = isIOS();
    if (ios) {
      const key = "pwa_install_hint_dismissed";
      const t = setTimeout(() => {
        if (!sessionStorage.getItem(key)) setShowIOSHint(true);
      }, 1500);
      return () => {
        clearTimeout(t);
        window.removeEventListener("beforeinstallprompt", handler);
      };
    }

    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, [dismissed]);

  const handleInstall = () => {
    if (prompt && "prompt" in prompt) {
      (prompt as { prompt: () => Promise<void> }).prompt();
      setVisible(false);
    }
  };

  const dismissIOSHint = () => {
    setShowIOSHint(false);
    setDismissed(true);
    try {
      sessionStorage.setItem("pwa_install_hint_dismissed", "1");
    } catch {
      // ignore
    }
  };

  if (isStandalone()) return null;

  if (showIOSHint) {
    return (
      <div className="fixed bottom-4 left-4 right-4 z-50 sm:left-auto sm:right-4 sm:max-w-sm">
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-lg border border-gray-200 dark:border-neutral-600 p-4">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            Instalar este app no tablet/celular
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            Toque no ícone <strong>Compartilhar</strong> (ou Enviar) na barra do navegador e depois em &quot;Adicionar à Tela de Início&quot;.
          </p>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={dismissIOSHint}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!visible || !prompt) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      <p className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-neutral-800 px-3 py-1 rounded-lg shadow-sm max-w-[200px] border border-gray-200 dark:border-neutral-600">
        Instale o app para acessar mais rápido
      </p>
      <button
        type="button"
        onClick={handleInstall}
        className="flex items-center gap-2 bg-[#ec4899] hover:bg-[#db2777] text-white px-4 py-2.5 rounded-xl shadow-lg font-medium transition-colors"
      >
        <span aria-hidden>📲</span>
        Instalar App
      </button>
    </div>
  );
}
