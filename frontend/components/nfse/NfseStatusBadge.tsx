'use client';

import { Badge } from '@/components/ui/badge';

const STATUS_CONFIG: Record<
  string,
  { variant: 'default' | 'destructive' | 'secondary'; className?: string; label: string }
> = {
  emitida: { variant: 'default', className: 'bg-green-600', label: 'Emitida' },
  cancelada: { variant: 'destructive', label: 'Cancelada' },
  erro: { variant: 'destructive', label: 'Erro' },
  pendente: { variant: 'secondary', label: 'Pendente' },
};

export function NfseStatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status];
  if (!config) {
    return <Badge variant="secondary">{status}</Badge>;
  }
  return (
    <Badge variant={config.variant} className={config.className}>
      {config.label}
    </Badge>
  );
}
