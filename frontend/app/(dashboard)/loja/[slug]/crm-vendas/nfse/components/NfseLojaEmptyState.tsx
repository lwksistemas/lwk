'use client';

import { FileText, Plus } from 'lucide-react';

export function NfseLojaEmptyState({
  hasFiltros,
  onEmitir,
}: {
  hasFiltros: boolean;
  onEmitir: () => void;
}) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-12 text-center">
      <FileText size={48} className="mx-auto text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Nenhuma nota fiscal encontrada</h3>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        {hasFiltros ? 'Tente ajustar os filtros de busca' : 'Comece emitindo sua primeira NFS-e'}
      </p>
      {!hasFiltros && (
        <button
          onClick={onEmitir}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90"
        >
          <Plus size={20} /> Emitir NFS-e
        </button>
      )}
    </div>
  );
}
