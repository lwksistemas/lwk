'use client';

import { Button } from '@/components/ui/button';
import { NFSE_FILTRO_STATUS_OPCOES } from '@/lib/nfse-constants';

export function NfseLojaFilters({
  filtroStatus,
  setFiltroStatus,
}: {
  filtroStatus: string;
  setFiltroStatus: (v: string) => void;
}) {
  return (
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
  );
}
