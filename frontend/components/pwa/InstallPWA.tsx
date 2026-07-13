"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

/**
 * Determina se o PWA deve ser oferecido nesta rota.
 * Oferece em: /loja/[slug]/..., /superadmin/login, /suporte/login
 * NÃO oferece em: homepage (/), /superadmin/* (exceto login), /suporte/* (exceto login)
 */
function getPWAContext(pathname: string | null): { allow: boolean; type: 'loja' | 'superadmin' | 'suporte' | null } {
  if (!pathname) return { allow: false, type: null };
  
  // Superadmin login
  if (pathname === '/superadmin/login') return { allow: true, type: 'superadmin' };
  
  // Suporte login
  if (pathname === '/suporte/login') return { allow: true, type: 'suporte' };
  
  // Loja
  const parts = pathname.split("/").filter(Boolean);
  if (parts[0] === "loja" && parts.length >= 2) {
    const seg = parts[1];
    if (seg === "dashboard" || seg === "trocar-senha") return { allow: false, type: null };
    return { allow: true, type: 'loja' };
  }
  
  return { allow: false, type: null };
}

// Mantém compatibilidade com código existente
export function isInstallPWALojaPath(pathname: string | null): boolean {
  return getPWAContext(pathname).allow;
}

declare global {
  interface Navigator {
    standalone?: boolean;
  }
  interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice?: Promise<{ outcome: "accepted" | "dismissed" }>;
  }
}

function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

function isIOS(): boolean {
  if (typeof navigator === "undefined") return false;
  return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

export function InstallPWA() {
  const pathname = usePathname();
  const { allow, type } = getPWAContext(pathname);

  const [prompt, setPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);
  const [showIOSHint, setShowIOSHint] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Verificar se já foi dismissado nesta sessão
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const key = `pwa_dismissed_${type || 'default'}`;
      const dismissedInSession = sessionStorage.getItem(key);
      if (dismissedInSession) setDismissed(true);
    }
  }, [type]);

  // Trocar manifest e registrar Service Worker conforme o contexto
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Registrar Service Worker apenas quando a geração do PWA estiver habilitada.
    if (process.env.NEXT_PUBLIC_PWA_ENABLED === 'true' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    let manifestUrl = '/manifest.json';
    if (type === 'superadmin') manifestUrl = '/manifest-superadmin.json';
    else if (type === 'suporte') manifestUrl = '/manifest-suporte.json';
    else if (type === 'loja') return; // Loja usa manifest dinâmico

    let link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'manifest';
      document.head.appendChild(link);
    }
    if (link.getAttribute('href') !== manifestUrl) {
      link.setAttribute('href', manifestUrl);
    }
  }, [type]);

  useEffect(() => {
    if (!allow) {
      setVisible(false);
      setPrompt(null);
      setShowIOSHint(false);
    }
  }, [allow]);

  useEffect(() => {
    if (isStandalone() || dismissed || !allow) return;

    const handler = (e: BeforeInstallPromptEvent) => {
      e.preventDefault();
      setPrompt(e);
      setVisible(true);
    };
    window.addEventListener("beforeinstallprompt", handler as EventListener);

    const ios = isIOS();
    if (ios) {
      const key = `pwa_ios_dismissed_${type || 'default'}`;
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
        window.removeEventListener("beforeinstallprompt", handler as EventListener);
      };
    }

    return () => window.removeEventListener("beforeinstallprompt", handler as EventListener);
  }, [dismissed, allow, type]);

  const handleInstall = () => {
    if (prompt) {
      void prompt.prompt();
      setVisible(false);
    }
  };

  const dismiss = () => {
    setVisible(false);
    setShowIOSHint(false);
    setDismissed(true);
    try {
      const key = `pwa_dismissed_${type || 'default'}`;
      sessionStorage.setItem(key, '1');
      if (isIOS()) {
        localStorage.setItem(`pwa_ios_dismissed_${type || 'default'}`, String(Date.now()));
      }
    } catch {
      // ignore
    }
  };

  if (isStandalone()) return null;
  if (!allow) return null;

  // Texto personalizado por tipo
  const appName = type === 'superadmin' ? 'LWK Admin' : type === 'suporte' ? 'LWK Suporte' : 'App da Loja';

  if (showIOSHint) {
    return (
      <div className="fixed bottom-4 left-4 right-4 z-[9999] sm:left-auto sm:right-4 sm:max-w-md">
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl border-2 border-gray-200 dark:border-neutral-600 p-4">
          <p className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">
            📲 Instalar {appName}
          </p>
          <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">
            Toque no ícone <strong>Compartilhar</strong> (quadrado com seta para cima) na barra inferior do Safari e depois em <strong>&quot;Adicionar à Tela de Início&quot;</strong>.
          </p>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={dismiss} className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
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
        <button type="button" onClick={dismiss} className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors" aria-label="Fechar">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div className="pr-6">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
            📲 Instalar {appName}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
            Acesse mais rápido instalando o app no seu dispositivo
          </p>
          <button type="button" onClick={handleInstall} className="w-full flex items-center justify-center gap-2 bg-[#0176d3] hover:bg-[#0159a8] text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm">
            <span aria-hidden>📲</span>
            Instalar Agora
          </button>
        </div>
      </div>
    </div>
  );
}
