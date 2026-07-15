'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { ClinicaBelezaNFSeConfigProvider } from '@/contexts/ClinicaBelezaNFSeConfigContext';
import ClinicaNFSeForm from '@/app/(dashboard)/loja/[slug]/clinica-beleza/configuracoes/nota-fiscal/ClinicaNFSeForm';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';

export default function SalaoNotaFiscalPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/cabeleireiro/configuracoes`;

  return (
    <ClinicaBelezaNFSeConfigProvider>
      <div className="p-4 md:p-6 space-y-4">
        <Link
          href={base}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:underline"
        >
          <ArrowLeft size={16} style={{ color: SALAO_PRIMARY }} />
          Voltar às configurações
        </Link>
        <ClinicaNFSeForm configBackHref={base} />
      </div>
    </ClinicaBelezaNFSeConfigProvider>
  );
}
