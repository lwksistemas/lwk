'use client';

import { ProcedimentosPageContent } from '@/components/clinica-beleza/ProcedimentosPageContent';
import { useParams } from 'next/navigation';

export default function EsteticaProcedimentosPage() {
  const slug = useParams().slug as string;
  return (
    <ProcedimentosPageContent
      title="Estética — Procedimentos"
      subtitle="Tratamentos estéticos oferecidos"
      defaultCategoria="estetica"
      backHref={`/loja/${slug}/dashboard`}
      relatedLinks={[
        { label: 'Profissionais', href: `/loja/${slug}/clinica-beleza/profissionais` },
        { label: 'Agenda', href: `/loja/${slug}/agenda` },
      ]}
    />
  );
}
