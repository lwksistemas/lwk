'use client';

import { ConfiguracoesSecaoPage } from '@/components/clinica-geral/ConfiguracoesSecaoPage';

export default function Page() {
  return (
    <ConfiguracoesSecaoPage
      titulo="Configurações de impressão"
      texto="Margens, cabeçalho e rodapé das receitas e documentos."
    />
  );
}
