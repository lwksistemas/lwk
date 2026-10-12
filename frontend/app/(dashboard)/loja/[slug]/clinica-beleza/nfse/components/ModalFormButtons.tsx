'use client';

/**
 * Botões de ação do modal (Voltar, Cancelar, Submit).
 */

interface ModalFormButtonsProps {
  loading: boolean;
  onBack: () => void;
  onClose: () => void;
  submitLabel?: string;
  loadingLabel?: string;
}

export function ModalFormButtons({
  loading,
  onBack,
  onClose,
  submitLabel = 'Emitir NFS-e',
  loadingLabel = 'Emitindo...',
}: ModalFormButtonsProps) {
  return (
    <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
      <button
        type="button"
        onClick={onBack}
        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
      >
        Voltar
      </button>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? loadingLabel : submitLabel}
        </button>
      </div>
    </div>
  );
}
