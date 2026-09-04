'use client';

import { Suspense } from 'react';
import { AgendaPage } from '@/components/clinica-geral/AgendaPage';

export default function ClinicaGeralAgendaRoute() {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-slate-500">Carregando agenda...</p>}>
      <AgendaPage />
    </Suspense>
  );
}
