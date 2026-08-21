"use client";

import { useLayoutEffect } from "react";

const ROOT_ID = "assinar-consentimento-root";

/** Link de e-mail/WhatsApp deve ficar claro no celular, igual no computador. */
export function forcarTemaClaroAssinatura() {
  if (typeof document === "undefined") return;
  const html = document.documentElement;
  html.classList.remove("dark");
  html.classList.add("light");
  html.style.colorScheme = "only light";
  const el = document.getElementById(ROOT_ID);
  if (!el) return;
  el.classList.remove("dark");
  el.style.colorScheme = "only light";
}

export function AssinarConsentimentoThemeSync() {
  useLayoutEffect(() => {
    forcarTemaClaroAssinatura();
    const html = document.documentElement;
    const observer = new MutationObserver(() => {
      if (html.classList.contains("dark")) forcarTemaClaroAssinatura();
    });
    observer.observe(html, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);
  return null;
}
