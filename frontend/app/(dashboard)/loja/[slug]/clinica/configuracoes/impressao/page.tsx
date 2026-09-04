'use client';

import { ConfiguracoesSecaoPage } from '@/components/clinica-geral/ConfiguracoesSecaoPage';

export default function ClinicaImpressaoRoute() {
  return (
    <ConfiguracoesSecaoPage
      titulo="Configurações de impressão"
      texto="Cabeçalho, rodapé e modelos de impressão do consultório entram neste espaço no próximo passo."
    />
  );
}
