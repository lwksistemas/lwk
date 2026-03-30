'use client';

import { X } from 'lucide-react';

interface CrmConfirmDeleteModalProps {
  tituloItem: string;
  enviando: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

/**
 * Modal de confirmação de exclusão (padrão CRM).
 */
export default function CrmConfirmDeleteModal({
  tituloItem,
  enviando,
  onClose,
  onConfirm,
}: CrmConfirmDeleteModalProps) {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !enviando && onClose()} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Excluir</h2>
            <button type="button" onClick={() => !enviando && onClose()} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
              <X size={20} />
            </button>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400">Deseja excluir &quot;{tituloItem}&quot;?</p>
              <div className="flex gap-2">
                <button type="button" onClick={onClose} className="flex-1 px-4 py-2 border rounded-lg">
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={onConfirm}
                  disabled={enviando}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                >
                  {enviando ? 'Excluindo...' : 'Excluir'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
