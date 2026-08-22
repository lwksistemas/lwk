'use client';

import { Suspense } from 'react';
import { PacientesPage } from '@/components/clinica-geral/PacientesPage';

export default function ClinicaGeralPacientesRoute() {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-slate-500">Carregando pacientes...</p>}>
      <PacientesPage />
    </Suspense>
  );
}
