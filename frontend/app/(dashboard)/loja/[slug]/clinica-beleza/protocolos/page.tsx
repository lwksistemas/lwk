'use client';

import { ProtocolosPageContent } from '@/components/clinica-beleza/protocolos-page/ProtocolosPageContent';
import { useParams } from 'next/navigation';

export default function ProtocolosPage() {
  const slug = useParams().slug as string;
  return (
    <ProtocolosPageContent
      title="Protocolos"
      subtitle="Todos os protocolos da clínica, de qualquer módulo"
      relatedLinks={[
        { label: 'Soroterapia — protocolos', href: `/loja/${slug}/clinica-beleza/soroterapia/protocolos` },
      ]}
    />
  );
}
