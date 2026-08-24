'use client';

import { ConfiguracoesSecaoPage } from '@/components/clinica-geral/ConfiguracoesSecaoPage';

export default function ClinicaProntuarioConfigRoute() {
  return (
    <ConfiguracoesSecaoPage
      titulo="Prontuário"
      texto="Ajustes do prontuário eletrônico (modelos e campos) entram neste espaço no próximo passo."
    />
  );
}
