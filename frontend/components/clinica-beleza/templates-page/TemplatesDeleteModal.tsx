import { X } from "lucide-react";
import type { DocumentTemplateItem } from "@/lib/clinica-beleza-api";

interface TemplatesDeleteModalProps {
  target: DocumentTemplateItem;
  deleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function TemplatesDeleteModal({ target, deleting, onClose, onConfirm }: TemplatesDeleteModalProps) {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !deleting && onClose()} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-lg w-full">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-neutral-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Excluir Template</h2>
            <button
              type="button"
              onClick={() => !deleting && onClose()}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-neutral-700"
            >
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
          </div>
          <div className="p-6">
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Deseja excluir o template &quot;{target.nome}&quot;? Ele será desativado e não aparecerá mais na
              listagem, mas ficará preservado para referência histórica.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => !deleting && onClose()}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-neutral-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onConfirm}
                disabled={deleting}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
              >
                {deleting ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
