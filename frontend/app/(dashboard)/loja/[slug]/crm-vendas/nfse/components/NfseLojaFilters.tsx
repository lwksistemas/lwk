'use client';

import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { NFSE_FILTRO_STATUS_OPCOES } from '@/lib/nfse-constants';

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
    <div className="space-y-3">
      <div className="flex gap-2 flex-wrap">
        {NFSE_FILTRO_STATUS_OPCOES.map(({ value, label }) => (
          <Button
            key={value || 'all'}
            variant={filtroStatus === value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFiltroStatus(value)}
          >
            {label}
          </Button>
        ))}
      </div>
      <div className="relative max-w-md">
        <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar por número, cliente ou CPF/CNPJ..."
          className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white"
        />
      </div>
    </div>
  );
}
