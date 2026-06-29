"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { ESTOQUE_INPUT_CLASS, type EstoqueProduto } from "@/components/clinica-beleza/estoque/estoque-types";

interface Props {
  produto: EstoqueProduto;
  tipo: "entrada" | "saida";
  saving: boolean;
  onClose: () => void;
  onSubmit: (quantidade: number, motivo: string) => Promise<void>;
}

export function EstoqueMovimentacaoModal({ produto, tipo, saving, onClose, onSubmit }: Props) {
  const [quantidade, setQuantidade] = useState(1);
  const [motivo, setMotivo] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(quantidade, motivo);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {tipo === "entrada" ? "Entrada de Estoque" : "Saída de Estoque"}
          </h2>
          <button type="button" onClick={onClose} className="p-1 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
            <X size={20} className="text-gray-500 dark:text-gray-400" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Produto: <span className="font-medium text-gray-900 dark:text-gray-100">{produto.nome}</span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Estoque atual: <span className="font-medium">{produto.quantidade_atual}</span>
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantidade</label>
            <input
              type="number"
              min={1}
              required
              value={quantidade}
              onChange={(e) => setQuantidade(Number(e.target.value))}
              className={ESTOQUE_INPUT_CLASS}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Motivo</label>
            <input
              type="text"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Ex: Compra fornecedor, Uso em procedimento..."
              className={ESTOQUE_INPUT_CLASS}
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className={`w-full py-2 text-white rounded-lg font-medium disabled:opacity-50 ${
              tipo === "entrada" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700"
            }`}
          >
            {saving ? "Registrando..." : tipo === "entrada" ? "Registrar Entrada" : "Registrar Saída"}
          </button>
        </form>
      </div>
    </div>
  );
}
