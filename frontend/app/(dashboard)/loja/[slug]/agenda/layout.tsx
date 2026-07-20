'use client';

import { ClinicaBelezaLojaLayout } from '@/components/clinica-beleza/ClinicaBelezaLojaLayout';

export default function AgendaLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClinicaBelezaLojaLayout
      loadingVariant="branded"
      mainClassName="flex flex-col flex-1 min-h-0 !overflow-hidden"
    >
      {children}
    </ClinicaBelezaLojaLayout>
  );
}
