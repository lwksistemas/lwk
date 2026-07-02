'use client';

import { X } from 'lucide-react';
import OportunidadeFormFields from '@/components/crm-vendas/OportunidadeFormFields';
import { useOportunidadeForm } from '@/hooks/crm-vendas/useOportunidadeForm';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  slug: string;
  etapas: { key: string; label: string }[];
  initialLeadId?: string;
}

export default function ModalCriarOportunidade({ open, onClose, onSuccess, slug, etapas, initialLeadId }: Props) {
  const formState = useOportunidadeForm({ initialLeadId, enabled: open });
  const { enviando, formErro, criarOportunidade } = formState;

  const handleCriarOportunidade = async (e: React.FormEvent) => {
    e.preventDefault();
    const id = await criarOportunidade();
    if (id) {
      onClose();
      onSuccess();
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-0 bg-black/50"
      onClick={() => !enviando && onClose()}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md max-h-[90vh] overflow-y-auto md:w-[calc(100vw-2rem)] md:max-w-4xl md:h-[calc(100vh-2rem)] md:max-h-none md:rounded-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Nova oportunidade</h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleCriarOportunidade} className="p-4 space-y-4">
          {formErro && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
              {formErro}
            </p>
          )}
          <OportunidadeFormFields slug={slug} etapas={etapas} layout="modal" formState={formState} />
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => !enviando && onClose()}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={enviando}
              className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium"
            >
              {enviando ? 'Criando...' : 'Criar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
