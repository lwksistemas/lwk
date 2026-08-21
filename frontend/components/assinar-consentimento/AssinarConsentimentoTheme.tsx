"use client";

import { useEffect } from "react";

const ROOT_ID = "assinar-consentimento-root";

function applySystemDark(el: HTMLElement) {
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  el.classList.toggle("dark", dark);
  el.style.colorScheme = dark ? "dark" : "light";
}

/** Reaplica o tema se o celular mudar claro/escuro com a página aberta. */
export function AssinarConsentimentoThemeSync() {
  useEffect(() => {
    const el = document.getElementById(ROOT_ID);
    if (!el) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applySystemDark(el);
    applySystemDark(el);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return null;
}
