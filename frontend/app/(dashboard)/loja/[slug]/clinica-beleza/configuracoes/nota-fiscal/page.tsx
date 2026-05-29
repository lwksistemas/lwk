'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { CRMConfigProvider } from '@/contexts/CRMConfigContext';
import ConfiguracaoNotaFiscalPage from '@/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/nota-fiscal/page';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

export default function ClinicaBelezaNotaFiscalPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;

  return (
    <CRMConfigProvider>
      <div className="space-y-4 p-4 md:p-6 max-w-5xl mx-auto">
        <Link
          href={base}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
        >
          <ArrowLeft size={16} style={{ color: CLINICA_BELEZA_PRIMARY }} />
          Voltar às configurações
        </Link>
        <ConfiguracaoNotaFiscalPage />
      </div>
    </CRMConfigProvider>
  );
}
