"use client";

import { useEffect, useState } from "react";

export function InstallPWA() {
  const [prompt, setPrompt] = useState<{ prompt: () => Promise<void> } | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      const ev = e as unknown as { prompt: () => Promise<void> };
      setPrompt(ev);
      setVisible(true);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = () => {
    if (prompt && "prompt" in prompt) {
      (prompt as { prompt: () => Promise<void> }).prompt();
      setVisible(false);
    }
  };

  if (!visible || !prompt) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      <p className="text-xs text-gray-600 bg-white/90 px-3 py-1 rounded-lg shadow-sm max-w-[200px]">
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
