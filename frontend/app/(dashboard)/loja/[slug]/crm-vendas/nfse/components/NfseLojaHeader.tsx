'use client';

import { FileText, Plus } from 'lucide-react';

export function NfseLojaHeader({ onEmitir }: { onEmitir: () => void }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} /> Notas Fiscais (NFS-e)
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Gerencie as notas fiscais emitidas para seus clientes
        </p>
      </div>
      <button
        onClick={onEmitir}
        className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 transition-colors"
      >
        <Plus size={20} /> Emitir NFS-e
      </button>
    </div>
  );
}
