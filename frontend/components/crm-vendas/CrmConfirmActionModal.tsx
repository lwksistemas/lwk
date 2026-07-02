'use client';

import { X } from 'lucide-react';

export type CrmConfirmVariant = 'danger' | 'primary';

export interface CrmConfirmActionModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  variant?: CrmConfirmVariant;
  loading?: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

/**
 * Modal de confirmação genérico (ações além de exclusão simples).
 */
export default function CrmConfirmActionModal({
  open,
  title,
  message,
  confirmLabel = 'Confirmar',
  variant = 'primary',
  loading = false,
  onClose,
  onConfirm,
}: CrmConfirmActionModalProps) {
  if (!open) return null;

  const confirmClass =
    variant === 'danger'
      ? 'bg-red-600 hover:bg-red-700'
      : 'bg-[#0176d3] hover:bg-[#0159a8]';

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[80]" onClick={() => !loading && onClose()} />
      <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
            <button
              type="button"
              onClick={() => !loading && onClose()}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X size={20} />
            </button>
          </div>
          <div className="p-6 space-y-4">
            <p className="text-gray-600 dark:text-gray-400 whitespace-pre-line">{message}</p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 px-4 py-2 border rounded-lg disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={onConfirm}
                disabled={loading}
                className={`flex-1 px-4 py-2 text-white rounded-lg disabled:opacity-50 ${confirmClass}`}
              >
                {loading ? 'Processando...' : confirmLabel}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
