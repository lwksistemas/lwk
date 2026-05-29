'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

type ModuleSegment = 'soroterapia' | 'estetica';

export function ClinicaBelezaModuleRedirect({ module: moduleSegment }: { module: ModuleSegment }) {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;

  useEffect(() => {
    router.replace(`/loja/${slug}/clinica-beleza/${moduleSegment}/procedimentos`);
  }, [slug, moduleSegment, router]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
      Redirecionando…
    </div>
  );
}
