'use client';

interface ModalLeadExcluirProps {
  lead: { nome: string };
  excluindo: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export default function ModalLeadExcluir({ lead, excluindo, onConfirm, onClose }: ModalLeadExcluirProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={() => !excluindo && onClose()}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-sm p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Excluir lead?</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Tem certeza que deseja excluir <strong>{lead.nome}</strong>? Esta ação não pode ser desfeita.
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => !excluindo && onClose()}
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={excluindo}
            className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium"
          >
            {excluindo ? 'Excluindo...' : 'Excluir'}
          </button>
        </div>
      </div>
    </div>
  );
}
