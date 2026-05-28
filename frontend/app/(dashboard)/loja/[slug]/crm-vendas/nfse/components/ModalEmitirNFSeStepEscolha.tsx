'use client';

import { FileText, Plus } from 'lucide-react';

export function ModalEmitirNFSeStepEscolha({
  onSelectConta,
  onSelectManual,
  onClose,
}: {
  onSelectConta: () => void;
  onSelectManual: () => void;
  onClose: () => void;
}) {
  return (
    <div className="space-y-4">
      <p className="text-gray-600 dark:text-gray-400 mb-6">Como deseja preencher os dados do cliente?</p>
      <button
        onClick={onSelectConta}
        className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 bg-[#0176d3]/10 rounded-lg">
            <FileText size={24} className="text-[#0176d3]" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Selecionar Cliente Cadastrado</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Escolha uma empresa ou pessoa física já cadastrada no CRM.
            </p>
          </div>
        </div>
      </button>
      <button
        onClick={onSelectManual}
        className="w-full p-6 border-2 border-gray-200 dark:border-gray-600 rounded-lg hover:border-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/10 transition-all text-left"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 bg-[#0176d3]/10 rounded-lg">
            <Plus size={24} className="text-[#0176d3]" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Preencher Manualmente</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Digite os dados do cliente manualmente.</p>
          </div>
        </div>
      </button>
      <div className="flex justify-end pt-4">
        <button
          onClick={onClose}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
