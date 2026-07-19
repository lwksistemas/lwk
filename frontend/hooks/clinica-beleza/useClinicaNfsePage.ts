'use client';

import { useClinicaNFSeConfig } from '@/contexts/ClinicaBelezaNFSeConfigContext';
import { useNfseLojaPage } from '@/hooks/useNfseLojaPage';

export function useClinicaNfsePage() {
  const { config } = useClinicaNFSeConfig();
  return useNfseLojaPage(config?.provedor_nf);
}
