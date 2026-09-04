'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { ConveniosConsultorioPage } from '@/components/clinica-geral/ConveniosConsultorioPage';

export default function ClinicaConveniosRoute() {
  return (
    <ConfiguracoesLayout>
      <ConveniosConsultorioPage />
    </ConfiguracoesLayout>
  );
}
