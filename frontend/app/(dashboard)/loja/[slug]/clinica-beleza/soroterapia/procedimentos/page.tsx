'use client';

import { ProcedimentosPageContent } from '@/components/clinica-beleza/ProcedimentosPageContent';
import { useParams } from 'next/navigation';

export default function SoroterapiaProcedimentosPage() {
  const slug = useParams().slug as string;
  return (
    <ProcedimentosPageContent
      title="Soroterapia — Procedimentos"
      subtitle="Soros e protocolos de soroterapia"
      defaultCategoria="soroterapia"
      backHref={`/loja/${slug}/dashboard`}
      relatedLinks={[{ label: 'Agenda', href: `/loja/${slug}/agenda` }]}
    />
  );
}
