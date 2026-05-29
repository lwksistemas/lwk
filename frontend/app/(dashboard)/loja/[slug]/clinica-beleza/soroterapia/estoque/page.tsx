'use client';

import { EstoquePageContent } from '@/components/clinica-beleza/EstoquePageContent';
import { useParams } from 'next/navigation';

export default function SoroterapiaEstoquePage() {
  const slug = useParams().slug as string;
  return (
    <EstoquePageContent
      title="Soroterapia — Estoque"
      subtitle="Ampolas, soros e insumos"
      defaultCategoria="soroterapia"
      backHref={`/loja/${slug}/dashboard`}
      relatedLinks={[{ label: 'Estoque geral', href: `/loja/${slug}/clinica-beleza/estoque` }]}
    />
  );
}
