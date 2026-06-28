'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { isTipoClinicaBeleza } from '@/lib/loja-tipo';
import { CrmVendasShell } from '@/components/crm-vendas/CrmVendasShell';

export default function CrmVendasLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    if (!slug) return;
    apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`)
      .then((r) => {
        const tipo = (r.data as { tipo_loja_nome?: string })?.tipo_loja_nome || '';
        if (isTipoClinicaBeleza(tipo)) {
          // Clínica não pode acessar CRM
          router.replace(`/loja/${slug}/dashboard`);
          setAllowed(false);
        } else {
          setAllowed(true);
        }
      })
      .catch(() => setAllowed(true)); // Em caso de erro, deixa passar (backend bloqueia)
  }, [slug, router]);

  if (allowed === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (!allowed) return null;

  return <CrmVendasShell>{children}</CrmVendasShell>;
}
