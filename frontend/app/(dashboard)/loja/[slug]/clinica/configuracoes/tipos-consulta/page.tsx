'use client';

import { ConfiguracoesSecaoPage } from '@/components/clinica-geral/ConfiguracoesSecaoPage';

export default function ClinicaTiposConsultaRoute() {
  return (
    <ConfiguracoesSecaoPage
      titulo="Tipos de consulta"
      texto="Os tipos de consulta (primeira, retorno, particular) serão configurados aqui no próximo passo."
    />
  );
}
