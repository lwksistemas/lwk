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
      const cooldownDays = 7;
      const t = setTimeout(() => {
        try {
          const raw = localStorage.getItem(key);
          const last = raw ? parseInt(raw, 10) : 0;
          if (Date.now() - last > cooldownDays * 24 * 60 * 60 * 1000) setShowIOSHint(true);
        } catch {
          setShowIOSHint(true);
        }
      }, 1200);
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
      localStorage.setItem("pwa_install_hint_dismissed", String(Date.now()));
    } catch {
      // ignore
    }
  };

  const dismissPrompt = () => {
    setVisible(false);
    setDismissed(true);
    try {
      localStorage.setItem("pwa_install_hint_dismissed", String(Date.now()));
    } catch {
      // ignore
    }
  };

  if (isStandalone()) return null;

  if (showIOSHint) {
    return (
      <div className="fixed bottom-4 left-4 right-4 z-[9999] sm:left-auto sm:right-4 sm:max-w-md">
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl border-2 border-gray-200 dark:border-neutral-600 p-4">
          <p className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">
            📲 Instalar app no iPhone
          </p>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
            Toque no ícone <strong>Compartilhar</strong> (quadrado com seta para cima) na barra inferior do Safari e depois em <strong>&quot;Adicionar à Tela de Início&quot;</strong>. O app abrirá direto na página desta loja.
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
    <div className="fixed bottom-4 right-4 z-50 max-w-[280px]">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl border border-gray-200 dark:border-neutral-600 p-4 relative">
        {/* Botão de fechar */}
        <button
          type="button"
          onClick={dismissPrompt}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
          aria-label="Fechar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Conteúdo */}
        <div className="pr-6">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
            📲 Instalar App
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
            Acesse mais rápido instalando o app no seu dispositivo
          </p>
          <button
            type="button"
            onClick={handleInstall}
            className="w-full flex items-center justify-center gap-2 bg-[#0176d3] hover:bg-[#0159a8] text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm"
          >
            <span aria-hidden>📲</span>
            Instalar Agora
          </button>
        </div>
      </div>
    </div>
  );
}
