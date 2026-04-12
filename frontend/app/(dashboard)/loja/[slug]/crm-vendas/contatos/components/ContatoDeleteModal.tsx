'use client';

import { Trash2 } from 'lucide-react';
import { ModalWrapper } from './ContatoFormModal';

interface Contato {
  id: number;
  nome: string;
  conta_nome?: string;
}

interface ContatoDeleteModalProps {
  contato: Contato;
  submitting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function ContatoDeleteModal({ contato, submitting, onClose, onConfirm }: ContatoDeleteModalProps) {
  return (
    <ModalWrapper title="Excluir Contato" onClose={onClose}>
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
          <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400">
            <Trash2 size={20} />
          </div>
          <div>
            <p className="font-medium text-red-900 dark:text-red-200">Tem certeza que deseja excluir este contato?</p>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">Esta ação não pode ser desfeita.</p>
          </div>
        </div>
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-sm font-medium text-gray-900 dark:text-white">{contato.nome}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{contato.conta_nome}</p>
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} disabled={submitting} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            Cancelar
          </button>
          <button type="button" onClick={onConfirm} disabled={submitting} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50">
            {submitting ? 'Excluindo...' : 'Excluir'}
          </button>
        </div>
      </div>
    </ModalWrapper>
  );
}
