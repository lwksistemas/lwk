import type { Campanha } from "./campanhas-page-types";

interface CampanhaExcluirModalProps {
  campanha: Campanha | null;
  excluindo: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function CampanhaExcluirModal({
  campanha,
  excluindo,
  onClose,
  onConfirm,
}: CampanhaExcluirModalProps) {
  if (!campanha) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Excluir campanha</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          Excluir <strong>{campanha.titulo}</strong>? Esta ação não pode ser desfeita.
        </p>
        <div className="flex gap-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={excluindo}
            className="flex-1 py-2.5 rounded-lg bg-red-600 text-white text-sm font-medium disabled:opacity-50"
          >
            {excluindo ? "Excluindo..." : "Excluir"}
          </button>
        </div>
      </div>
    </div>
  );
}
