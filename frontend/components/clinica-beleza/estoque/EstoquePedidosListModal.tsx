"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api/client";
import type { PedidoCompraItem } from "@/lib/clinica-beleza-api/client-ops";
import { extractEstoqueApiError } from "./estoque-types";

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
                <button
                  key={p.id}
                  type="button"
                  onClick={() => onOpenPedido(p.id)}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800"
                >
                  <div className="flex justify-between gap-2">
                    <span className="font-medium text-sm">Pedido nº {p.numero}</span>
                    <span className="text-xs text-gray-500">{p.status_display}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {p.fornecedor.nome_fantasia || p.fornecedor.razao_social} · R$ {p.valor_total}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
