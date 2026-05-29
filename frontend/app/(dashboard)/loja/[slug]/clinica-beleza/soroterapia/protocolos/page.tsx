'use client';

import { ProtocolosPageContent } from '@/components/clinica-beleza/ProtocolosPageContent';
import { useParams } from 'next/navigation';

export default function SoroterapiaProtocolosPage() {
  const slug = useParams().slug as string;
  return (
    <ProtocolosPageContent
      title="Soroterapia — Protocolos"
      subtitle="Etapas padronizadas para aplicação de soros"
      defaultCategoria="soroterapia"
      backHref={`/loja/${slug}/dashboard`}
      relatedLinks={[
        { label: 'Protocolos (geral)', href: `/loja/${slug}/clinica-beleza/protocolos` },
        { label: 'Agenda', href: `/loja/${slug}/agenda` },
      ]}
    />
  );
}
