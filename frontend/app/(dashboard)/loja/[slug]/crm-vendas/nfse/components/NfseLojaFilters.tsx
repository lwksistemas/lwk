'use client';

import { Search } from 'lucide-react';

export function NfseLojaFilters({
  busca,
  setBusca,
  filtroStatus,
  setFiltroStatus,
}: {
  busca: string;
  setBusca: (v: string) => void;
  filtroStatus: string;
  setFiltroStatus: (v: string) => void;
}) {
  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative">
          <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por número, cliente ou CPF/CNPJ..."
            className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
          />
        </div>
        <select
          value={filtroStatus}
          onChange={(e) => setFiltroStatus(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
        >
          <option value="">Todos os status</option>
          <option value="emitida">Emitida</option>
          <option value="cancelada">Cancelada</option>
          <option value="erro">Erro</option>
        </select>
      </div>
    </div>
  );
}
