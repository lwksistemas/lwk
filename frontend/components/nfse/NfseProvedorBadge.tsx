'use client';

import { Badge } from '@/components/ui/badge';
import { nfseProvedorLabel } from '@/lib/nfse-helpers';

export function NfseProvedorBadge({ provedor }: { provedor: string }) {
  return (
    <Badge variant="secondary" className="text-xs">
      {nfseProvedorLabel(provedor)}
    </Badge>
  );
}
