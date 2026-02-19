"use client";

import { useState } from "react";
import { useOnline } from "@/hooks/useOnline";
import { useSyncPending, notificarFilaAtualizada } from "@/hooks/useSyncPending";
import { limparFilaSync } from "@/lib/offline-db";
import { Trash2 } from "lucide-react";

/**
 * Indicador de status offline/online e fila de sincronização.
 * Exibir no header da agenda, dashboard, etc.
 */
export function OfflineIndicator() {
  const online = useOnline();
  const pendingCount = useSyncPending();
  const [clearing, setClearing] = useState(false);

  const handleClearQueue = async () => {
    if (!confirm(`Tem certeza que deseja limpar ${pendingCount} ${pendingCount === 1 ? 'item' : 'itens'} da fila?\n\nEsta ação não pode ser desfeita e os dados não sincronizados serão perdidos.`)) {
      return;
    }
    
    setClearing(true);
    try {
      await limparFilaSync();
      notificarFilaAtualizada();
      console.log("✅ [offline] Fila limpa com sucesso");
    } catch (error) {
      console.error("❌ [offline] Erro ao limpar fila:", error);
      alert("Erro ao limpar fila. Tente novamente.");
    } finally {
      setClearing(false);
    }
  };

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
      {pendingCount > 0 && (
        <>
          <span className="text-xs px-2 py-0.5 rounded bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300">
            {pendingCount} na fila
          </span>
          <button
            onClick={handleClearQueue}
            disabled={clearing}
            className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
            title="Limpar fila de sincronização"
          >
            <Trash2 size={16} />
          </button>
        </>
      )}
    </div>
  );
}
