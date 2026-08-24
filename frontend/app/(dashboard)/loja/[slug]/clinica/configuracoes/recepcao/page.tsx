'use client';

import { ConfiguracoesLayout } from '@/components/clinica-geral/ConfiguracoesLayout';
import { FuncionariosPage } from '@/components/clinica-geral/FuncionariosPage';

export default function ClinicaRecepcaoRoute() {
  return (
    <ConfiguracoesLayout>
      <FuncionariosPage />
    </ConfiguracoesLayout>
  );
}
