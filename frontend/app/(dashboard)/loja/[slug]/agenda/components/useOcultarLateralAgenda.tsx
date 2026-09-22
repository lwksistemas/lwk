"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "agenda-ocultar-lateral";

/** Preferência local: esconder o calendário e a lista Próximos para alargar a grade. */
export function useOcultarLateralAgenda() {
  const [ocultar, setOcultar] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      setOcultar(window.localStorage.getItem(STORAGE_KEY) === "1");
    } catch {
      /* ignore */
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, ocultar ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [ocultar, ready]);

  return { ocultar, setOcultar };
}

export function BotaoOcultarLateralAgenda({
  ocultar,
  onToggle,
}: {
  ocultar: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      className="hidden lg:inline-flex items-center px-3 h-8 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 hover:bg-gray-50"
      onClick={onToggle}
      aria-pressed={ocultar}
      title={ocultar ? "Mostrar calendário e próximos" : "Ocultar calendário e próximos"}
    >
      {ocultar ? "Mostrar" : "Ocultar"}
    </button>
  );
}
