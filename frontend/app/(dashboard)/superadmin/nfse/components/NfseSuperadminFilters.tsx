'use client';

import { Button } from '@/components/ui/button';
import { NFSE_FILTRO_STATUS_OPCOES } from '@/lib/nfse-constants';

export function NfseSuperadminFilters({
  filtroStatus,
  onFiltroChange,
}: {
  filtroStatus: string;
  onFiltroChange: (status: string) => void;
}) {
  return (
    <div className="flex gap-2">
      {NFSE_FILTRO_STATUS_OPCOES.map(({ value, label }) => (
        <Button
          key={value || 'all'}
          variant={filtroStatus === value ? 'default' : 'outline'}
          size="sm"
          onClick={() => onFiltroChange(value)}
        >
          {label}
        </Button>
      ))}
    </div>
  );
}
