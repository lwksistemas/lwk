"use client";

import { useState } from "react";
import { useOnline } from "@/hooks/useOnline";
import { useSyncPending, notificarFilaAtualizada } from "@/hooks/useSyncPending";
import { limparFilaSync, obterFilaSync } from "@/lib/offline-db";
import { Trash2, Info } from "lucide-react";

/**
 * Indicador de status offline/online e fila de sincronização.
 * Exibir no header da agenda, dashboard, etc.
 */
export function OfflineIndicator() {
  const online = useOnline();
  const pendingCount = useSyncPending();
  const [clearing, setClearing] = useState(false);
  const [showQueue, setShowQueue] = useState(false);
  const [queueItems, setQueueItems] = useState<any[]>([]);

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

  const handleShowQueue = async () => {
    try {
      const items = await obterFilaSync();
      setQueueItems(items);
      setShowQueue(true);
      console.log("📋 [offline] Itens na fila:", items);
    } catch (error) {
      console.error("❌ [offline] Erro ao buscar fila:", error);
      alert("Erro ao buscar fila. Abra o console (F12) para mais detalhes.");
    }
  };

  return (
    <>
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
              onClick={handleShowQueue}
              className="p-1.5 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
              title="Ver detalhes da fila"
            >
              <Info size={16} />
            </button>
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

      {/* Modal de Detalhes da Fila */}
      {showQueue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="sticky top-0 bg-white dark:bg-neutral-800 border-b border-gray-200 dark:border-neutral-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Fila de Sincronização ({queueItems.length} {queueItems.length === 1 ? 'item' : 'itens'})
              </h2>
              <button
                onClick={() => setShowQueue(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
              {queueItems.length === 0 ? (
                <p className="text-center text-gray-500 dark:text-gray-400">Fila vazia</p>
              ) : (
                <div className="space-y-4">
                  {queueItems.map((item, index) => (
                    <div
                      key={item.id || index}
                      className="p-4 border border-gray-200 dark:border-neutral-700 rounded-lg bg-gray-50 dark:bg-neutral-900"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {item.tipo.charAt(0).toUpperCase() + item.tipo.slice(1)}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          ID: {item.id}
                        </span>
                      </div>
                      <pre className="text-xs bg-white dark:bg-neutral-800 p-3 rounded border border-gray-200 dark:border-neutral-700 overflow-x-auto">
                        {JSON.stringify(item.payload, null, 2)}
                      </pre>
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        Criado: {new Date(item.createdAt).toLocaleString('pt-BR')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="sticky bottom-0 bg-gray-50 dark:bg-neutral-700/50 px-6 py-4 border-t border-gray-200 dark:border-neutral-700">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                💡 Dica: Abra o Console (F12) para ver logs detalhados de sincronização
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
