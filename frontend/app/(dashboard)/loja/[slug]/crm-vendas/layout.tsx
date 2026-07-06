'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { isTipoClinicaBeleza } from '@/lib/loja-tipo';
import { cacheLojaLoginContext } from '@/lib/login-default-backgrounds';
import { CrmVendasShell } from '@/components/crm-vendas/CrmVendasShell';

function lojaTipoCacheKey(slug: string) {
  return `loja_tipo_${slug}`;
}

export default function CrmVendasLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [layoutError, setLayoutError] = useState<string | null>(null);

  const verificarAcesso = useCallback(() => {
    if (!slug) return;
    setLayoutError(null);

    const cachedTipo =
      typeof window !== 'undefined' ? sessionStorage.getItem(lojaTipoCacheKey(slug)) : null;
    if (cachedTipo && isTipoClinicaBeleza(cachedTipo)) {
      router.replace(`/loja/${slug}/dashboard`);
      setAllowed(false);
      return;
    }

    apiClient
      .get(`/superadmin/lojas/info_publica/?slug=${slug}`)
      .then((r) => {
        const tipo = (r.data as { tipo_loja_nome?: string })?.tipo_loja_nome || '';
        cacheLojaLoginContext(slug, tipo);
        if (isTipoClinicaBeleza(tipo)) {
          router.replace(`/loja/${slug}/dashboard`);
          setAllowed(false);
        } else {
          setAllowed(true);
        }
      })
      .catch(() => {
        if (cachedTipo && !isTipoClinicaBeleza(cachedTipo)) {
          setAllowed(true);
          return;
        }
        setAllowed(false);
        setLayoutError('Não foi possível verificar o tipo da loja. Tente novamente.');
      });
  }, [slug, router]);

  useEffect(() => {
    verificarAcesso();
  }, [verificarAcesso]);

  if (allowed === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (layoutError) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-gray-50 dark:bg-gray-900 p-6">
        <p className="text-red-600 dark:text-red-400 text-center max-w-md">{layoutError}</p>
        <button
          type="button"
          onClick={verificarAcesso}
          className="px-4 py-2 rounded-lg bg-[#0176d3] text-white text-sm font-medium hover:bg-[#0159a8]"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if (!allowed) return null;

  return <CrmVendasShell>{children}</CrmVendasShell>;
}
