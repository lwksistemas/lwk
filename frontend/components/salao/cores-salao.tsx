"use client";

import { createContext, useContext } from "react";

export const STATUS_PADRAO: Record<string, string> = {
  SCHEDULED: "#a16207",
  CONFIRMED: "#1d4ed8",
  IN_PROGRESS: "#4c1d78",
  COMPLETED: "#1f8a4c",
  CANCELLED: "#b91c1c",
  NO_SHOW: "#6b7280",
};

export function hexCor(valor: string | undefined, padrao: string) {
  const texto = (valor || "").trim();
  return /^#[0-9A-Fa-f]{6}$/.test(texto) ? texto.toLowerCase() : padrao;
}

export function mapaStatus(bruto?: Record<string, { bg?: string }> | null) {
  const saida: Record<string, string> = {};
  for (const [codigo, padrao] of Object.entries(STATUS_PADRAO)) {
    saida[codigo] = hexCor(bruto?.[codigo]?.bg, padrao);
  }
  return saida;
}

const CoresContexto = createContext<Record<string, string>>(mapaStatus(null));

export function CoresStatusProvider({ cores, children }: { cores: Record<string, string>; children: React.ReactNode }) {
  return <CoresContexto.Provider value={cores}>{children}</CoresContexto.Provider>;
}

export function useStatusSalao() {
  return useContext(CoresContexto);
}
