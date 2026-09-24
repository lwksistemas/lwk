'use client';

import { ProtocolosPageContent } from '@/components/clinica-beleza/protocolos-page/ProtocolosPageContent';
import { useParams } from 'next/navigation';

export default function ProtocolosPage() {
  const slug = useParams().slug as string;
  return (
    <ProtocolosPageContent
      title="Protocolos"
      subtitle="Nome, sessões, produtos e cuidados. O valor fica no procedimento da categoria Protocolo."
      relatedLinks={[
        { label: 'Soroterapia — protocolos', href: `/loja/${slug}/clinica-beleza/soroterapia/protocolos` },
      ]}
    />
  );
}
