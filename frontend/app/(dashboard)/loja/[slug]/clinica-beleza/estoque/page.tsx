'use client';

import { EstoquePageContent } from '@/components/clinica-beleza/EstoquePageContent';
import { useParams } from 'next/navigation';

export default function EstoquePage() {
  const slug = useParams().slug as string;
  return (
    <EstoquePageContent
      title="Estoque geral"
      subtitle="Todos os produtos e insumos da clínica"
      relatedLinks={[
        { label: 'Estoque de soros (Soroterapia)', href: `/loja/${slug}/clinica-beleza/soroterapia/estoque` },
      ]}
    />
  );
}
