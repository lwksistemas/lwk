"use client";

import { useEffect, useState } from "react";
import { obterFilaSync } from "@/lib/offline-db";

/**
 * Retorna a quantidade de itens na fila de sincronização (pendentes de envio quando voltar online).
 */
export function useSyncPending(): number {
  const [count, setCount] = useState(0);

  const refresh = () => {
    obterFilaSync().then((list) => setCount(list.length));
  };

  useEffect(() => {
    refresh();
    window.addEventListener("online", refresh);
    window.addEventListener("offline-sync-done", refresh);
    window.addEventListener("fila-sync-updated", refresh);
    return () => {
      window.removeEventListener("online", refresh);
      window.removeEventListener("offline-sync-done", refresh);
      window.removeEventListener("fila-sync-updated", refresh);
    };
  }, []);

  return count;
}

export function notificarFilaAtualizada(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("fila-sync-updated"));
  }
}
