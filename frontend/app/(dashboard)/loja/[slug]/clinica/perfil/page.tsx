'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { PerfilPage } from '@/components/clinica-geral/PerfilPage';

export default function ClinicaPerfilRoute() {
  return (
    <ConfiguracoesLayout>
      <PerfilPage />
    </ConfiguracoesLayout>
  );
}
