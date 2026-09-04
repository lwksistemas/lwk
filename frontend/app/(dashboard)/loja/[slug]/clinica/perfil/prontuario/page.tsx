'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { ProntuarioConfigPage } from '@/components/clinica-geral/ProntuarioConfigPage';

export default function ClinicaProntuarioConfigRoute() {
  return (
    <ConfiguracoesLayout>
      <ProntuarioConfigPage />
    </ConfiguracoesLayout>
  );
}
