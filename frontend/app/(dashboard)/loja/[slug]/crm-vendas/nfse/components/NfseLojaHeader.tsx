'use client';

import { FileText, Plus, RefreshCw } from 'lucide-react';

export function NfseLojaHeader({
  onEmitir,
  onRecuperar,
}: {
  onEmitir: () => void;
  onRecuperar?: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 flex-wrap">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText size={28} /> Notas Fiscais (NFS-e)
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Gerencie as notas fiscais emitidas para seus clientes
        </p>
      </div>
      <div className="flex items-center gap-2">
        {onRecuperar && (
          <button
            type="button"
            onClick={onRecuperar}
            className="flex items-center gap-2 px-4 py-2 border border-[#0176d3] text-[#0176d3] dark:text-[#5eb0ff] dark:border-[#5eb0ff] rounded-lg hover:bg-[#0176d3]/10 transition-colors"
          >
            <RefreshCw size={18} /> Recuperar do ISSNet
          </button>
        )}
        <button
          type="button"
          onClick={onEmitir}
          className="flex items-center gap-2 px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 transition-colors"
        >
          <Plus size={20} /> Emitir NFS-e
        </button>
      </div>
    </div>
  );
}
