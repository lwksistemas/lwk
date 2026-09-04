'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { EspecialidadesPage } from '@/components/clinica-geral/EspecialidadesPage';

export default function ClinicaEspecialidadesRoute() {
  return (
    <ConfiguracoesLayout>
      <EspecialidadesPage />
    </ConfiguracoesLayout>
  );
}
