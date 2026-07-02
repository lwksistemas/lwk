'use client';

import { X } from 'lucide-react';
import { ContatoFormFields } from '@/components/crm-vendas/ContatoFormFields';
import type { CrmContatoFormData } from '@/lib/crm-contato-form-types';

interface ContatoFormModalProps {
  title: string;
  formData: CrmContatoFormData;
  contaNomeInicial?: string;
  submitting: boolean;
  onChange: (data: CrmContatoFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onClose: () => void;
}

export function ContatoFormModal({
  title,
  formData,
  contaNomeInicial,
  submitting,
  onChange,
  onSubmit,
  onClose,
}: ContatoFormModalProps) {
  return (
    <ModalWrapper title={title} onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <ContatoFormFields
          layout="modal"
          formData={formData}
          contaNomeInicial={contaNomeInicial}
          disabled={submitting}
          onChange={onChange}
        />
        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors disabled:opacity-50"
          >
            {submitting ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  );
}

export function ModalWrapper({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            >
              <X size={20} />
            </button>
          </div>
          <div className="p-6">{children}</div>
        </div>
      </div>
    </>
  );
}
