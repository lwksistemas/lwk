'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { RefreshCw } from 'lucide-react';

/** Redireciona para a página unificada de assinatura (padrão de todos os apps). */
export default function FinanceiroLojaRedirectPage() {
  const router = useRouter();
  const slug = useParams().slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/assinatura`);
  }, [router, slug]);

  return (
    <div className="min-h-[40vh] flex items-center justify-center">
      <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
    </div>
  );
}
