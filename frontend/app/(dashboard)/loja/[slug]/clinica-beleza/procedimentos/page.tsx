'use client';

import { ProcedimentosPageContent } from '@/components/clinica-beleza/procedimentos-page/ProcedimentosPageContent';
import { useParams } from 'next/navigation';

export default function ProcedimentosPage() {
  const slug = useParams().slug as string;
  return (
    <ProcedimentosPageContent
      relatedLinks={[
        { label: 'Soroterapia — procedimentos', href: `/loja/${slug}/clinica-beleza/soroterapia/procedimentos` },
      ]}
    />
  );
}
