"use client";

import { useEffect, useState } from "react";

const PWA_LOJA_SLUG_KEY = "pwa_loja_slug";

function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (window.navigator as { standalone?: boolean }).standalone === true
  );
}

export default function PwaRedirect({
  children,
}: {
  children: React.ReactNode;
}) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isStandalone()) {
      setReady(true);
      return;
    }
    const slug = localStorage.getItem(PWA_LOJA_SLUG_KEY);
    if (slug && slug.trim()) {
      window.location.replace(`/loja/${slug.trim()}/login`);
      return;
    }
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-gray-500">Carregando...</div>
      </div>
    );
  }

  return <>{children}</>;
}
