"use client";

import { X } from "lucide-react";
import type { DescricaoAlteracaoAgenda } from "@/lib/agenda-confirmar-alteracao";

export function ModalConfirmarAlteracaoAgenda({
  pedido,
  onConfirmar,
  onCancelar,
}: {
  pedido: DescricaoAlteracaoAgenda | null;
  onConfirmar: () => void;
  onCancelar: () => void;
}) {
  if (!pedido) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div
        className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmar-alteracao-agenda"
      >
        <div className="flex justify-between items-start mb-4">
          <h2 id="confirmar-alteracao-agenda" className="text-xl font-bold text-gray-800 dark:text-gray-100">
            {pedido.titulo}
          </h2>
          <button
            type="button"
            onClick={onCancelar}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
            aria-label="Cancelar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="space-y-2 mb-6">
          {pedido.linhas.map((linha) => (
            <p key={linha} className="text-sm text-gray-700 dark:text-gray-200">
              {linha}
            </p>
          ))}
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Nada é gravado até você confirmar.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onConfirmar}
            className="flex-1 px-4 py-2 text-white rounded-lg hover:opacity-90"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            Confirmar
          </button>
          <button
            type="button"
            onClick={onCancelar}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
