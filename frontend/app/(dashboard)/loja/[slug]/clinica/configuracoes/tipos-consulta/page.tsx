'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { TiposConsultaPage } from '@/components/clinica-geral/TiposConsultaPage';

export default function ClinicaTiposConsultaRoute() {
  return (
    <ConfiguracoesLayout>
      <TiposConsultaPage />
    </ConfiguracoesLayout>
  );
}
