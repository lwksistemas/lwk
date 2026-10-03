"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "lwk-clinica-dark";

function applyDarkToDocument(isDark: boolean) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.classList.toggle("dark", isDark);
  root.style.colorScheme = isDark ? "dark" : "only light";
}

/**
 * Tema (modo escuro) persistido em localStorage e aplicado em document,
 * para que todas as páginas da Clínica da Beleza usem o mesmo tema.
 */
export function useClinicaBelezaDark(): [boolean, (value: boolean) => void] {
  const [darkMode, setDarkModeState] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) === "true";
    setDarkModeState(stored);
    applyDarkToDocument(stored);
  }, []);

  const setDarkMode = (value: boolean) => {
    setDarkModeState(value);
    localStorage.setItem(STORAGE_KEY, value ? "true" : "false");
    applyDarkToDocument(value);
  };

  return [darkMode, setDarkMode];
}
