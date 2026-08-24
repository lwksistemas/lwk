'use client';

import { ConfiguracoesSecaoPage } from '@/components/clinica-geral/ConfiguracoesSecaoPage';

export default function Page() {
  return (
    <ConfiguracoesSecaoPage
      titulo="Tipos de consulta"
      texto="Defina os tipos de consulta (retorno, primeira vez, particular)."
    />
  );
}
