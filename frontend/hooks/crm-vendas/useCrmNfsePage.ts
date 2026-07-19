'use client';

import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useNfseLojaPage } from '@/hooks/useNfseLojaPage';

export type { NfseConfirmAction, NfseSyncMessage } from '@/hooks/useNfseLojaPage';

export function useCrmNfsePage() {
  const { config } = useCRMConfig();
  return useNfseLojaPage(config?.provedor_nf);
}
