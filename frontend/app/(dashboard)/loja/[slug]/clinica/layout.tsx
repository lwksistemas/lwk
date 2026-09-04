'use client';

import { Suspense } from 'react';
import { ClinicaGeralLojaLayout } from '@/components/clinica-geral/ClinicaGeralLojaLayout';

export default function ClinicaGeralLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<p className="p-6 text-sm text-slate-500">Carregando consultório...</p>}>
      <ClinicaGeralLojaLayout>{children}</ClinicaGeralLojaLayout>
    </Suspense>
  );
}
