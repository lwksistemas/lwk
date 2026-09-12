"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Trash2, X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api/client";
import type { PedidoCompraItem } from "@/lib/clinica-beleza-api/client-ops";
import { extractEstoqueApiError } from "./estoque-types";
import { numeroPedidoLabel } from "./pedido-compra-utils";

export function EstoquePedidosListModal({
  open,
  onClose,
  onOpenPedido,
}: {
  open: boolean;
  onClose: () => void;
  onOpenPedido: (id: number) => void;
}) {
  const [lista, setLista] = useState<PedidoCompraItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [excluindoId, setExcluindoId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const carregar = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setLista(await ClinicaBelezaAPI.estoque.pedidos.list());
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao carregar pedidos."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) void carregar();
  }, [open, carregar]);

  const excluir = async (p: PedidoCompraItem) => {
    if (!confirm(`Excluir o pedido nº ${numeroPedidoLabel(p.numero)}? Esta ação não pode ser desfeita.`)) return;
    setExcluindoId(p.id);
    setError("");
    try {
      await ClinicaBelezaAPI.estoque.pedidos.delete(p.id);
      setLista((atual) => atual.filter((item) => item.id !== p.id));
    } catch (err) {
      setError(extractEstoqueApiError(err, "Erro ao excluir pedido."));
    } finally {
      setExcluindoId(null);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <h2 className="text-lg font-semibold">Pedidos de compra</h2>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
            <X size={20} className="text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="animate-spin text-gray-400" /></div>
          ) : lista.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">Nenhum pedido.</p>
          ) : (
            <div className="space-y-2">
              {lista.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-2 p-3 rounded-lg border border-gray-200 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800"
                >
                  <button
                    type="button"
                    onClick={() => onOpenPedido(p.id)}
                    className="flex-1 text-left min-w-0"
                  >
                    <div className="flex justify-between gap-2">
                      <span className="font-medium text-sm">Pedido nº {numeroPedidoLabel(p.numero)}</span>
                      <span className="text-xs text-gray-500">{p.status_display}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {p.fornecedor.nome_fantasia || p.fornecedor.razao_social} · R$ {p.valor_total}
                    </p>
                  </button>
                  <button
                    type="button"
                    title="Excluir pedido"
                    disabled={excluindoId === p.id}
                    onClick={() => void excluir(p)}
                    className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 disabled:opacity-50"
                  >
                    {excluindoId === p.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
