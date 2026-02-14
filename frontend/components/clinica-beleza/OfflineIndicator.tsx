"use client";

import { useOnline } from "@/hooks/useOnline";
import { useSyncPending } from "@/hooks/useSyncPending";

/**
 * Indicador de status offline/online e fila de sincronização.
 * Exibir no header da agenda, dashboard, etc.
 */
export function OfflineIndicator() {
  const online = useOnline();
  const pendingCount = useSyncPending();

  return (
    <div className="flex items-center gap-2">
      <span
        className={`text-xs sm:text-sm px-2.5 py-1 rounded-full font-medium ${
          online
            ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
            : "bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300"
        }`}
        title={online ? "Conectado" : "Sem conexão — alterações serão enviadas quando voltar"}
      >
        {online ? "🟢 Online" : "🔴 Offline"}
      </span>
      {!online && pendingCount > 0 && (
        <span className="text-xs px-2 py-0.5 rounded bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300">
          {pendingCount} na fila
        </span>
      )}
    </div>
  );
}
