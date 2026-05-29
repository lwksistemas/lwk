'use client';

import { ProtocolosPageContent } from '@/components/clinica-beleza/ProtocolosPageContent';
import { useParams } from 'next/navigation';

export default function EsteticaProtocolosPage() {
  const slug = useParams().slug as string;
  return (
    <ProtocolosPageContent
      title="Estética — Protocolos"
      subtitle="Roteiros de tratamentos estéticos"
      defaultCategoria="estetica"
      backHref={`/loja/${slug}/dashboard`}
      relatedLinks={[
        { label: 'Protocolos (geral)', href: `/loja/${slug}/clinica-beleza/protocolos` },
        { label: 'Profissionais', href: `/loja/${slug}/clinica-beleza/profissionais` },
        { label: 'Agenda', href: `/loja/${slug}/agenda` },
      ]}
    />
  );
}
