'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

/** Compatibilidade: URL antiga redireciona para estoque unificado com filtro. */
export default function SoroterapiaEstoqueRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/clinica-beleza/estoque?categoria=soroterapia`);
  }, [slug, router]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
      Redirecionando…
    </div>
  );
}
