"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { logger } from "@/lib/logger";

interface SelectedBloqueio {
  id: number;
  motivo: string;
  professional_name: string;
}

interface ModalBloqueioProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  bloqueio: SelectedBloqueio | null;
}

export function ModalBloqueio({ open, onClose, onSuccess, bloqueio }: ModalBloqueioProps) {
  const [deleting, setDeleting] = useState(false);

  if (!open || !bloqueio) return null;

  const excluirBloqueio = async () => {
    if (!confirm(`Excluir o bloqueio "${bloqueio.motivo}"?`)) return;
    setDeleting(true);
    try {
      const res = await clinicaBelezaFetch(`/bloqueios/${bloqueio.id}/`, { method: "DELETE" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Erro ao excluir bloqueio");
      }
      onClose();
      onSuccess();
    } catch (error) {
      logger.warn("Erro ao excluir bloqueio:", error);
      alert(error instanceof Error ? error.message : "Erro ao excluir bloqueio.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">Bloqueio de horário</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-2">{bloqueio.motivo}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Profissional: {bloqueio.professional_name}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
          Arraste o bloqueio para outro horário ou puxe a borda inferior para ajustar a duração.
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={excluirBloqueio}
            disabled={deleting}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {deleting ? "Excluindo..." : "Excluir bloqueio"}
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
