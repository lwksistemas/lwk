'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { ClinicaBelezaNFSeConfigProvider } from '@/contexts/ClinicaBelezaNFSeConfigContext';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import ClinicaNFSeForm from './ClinicaNFSeForm';

export default function ClinicaBelezaNotaFiscalPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;

  return (
    <ClinicaBelezaNFSeConfigProvider>
      <ClinicaBelezaPageContent className="space-y-4">
        <Link
          href={base}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
        >
          <ArrowLeft size={16} style={{ color: CLINICA_BELEZA_PRIMARY }} />
          Voltar às configurações
        </Link>
        <ClinicaNFSeForm configBackHref={base} />
      </ClinicaBelezaPageContent>
    </ClinicaBelezaNFSeConfigProvider>
  );
}
